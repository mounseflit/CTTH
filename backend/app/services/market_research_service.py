"""Market research service: queries and LLM-based framework generation."""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# ── Simple in-memory TTL cache ────────────────────────────────
_svc_cache: dict = {}
_SVC_CACHE_TTL = 300  # 5 minutes


def _scache_get(key: str):
    entry = _svc_cache.get(key)
    if entry and (time.monotonic() - entry["ts"]) < _SVC_CACHE_TTL:
        return entry["data"]
    return None


def _scache_set(key: str, data):
    _svc_cache[key] = {"ts": time.monotonic(), "data": data}


def _format_value(val: float) -> str:
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1_000_000_000:
        return f"{sign}${abs_val / 1_000_000_000:.1f}B"
    if abs_val >= 1_000_000:
        return f"{sign}${abs_val / 1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"{sign}${abs_val / 1_000:.1f}K"
    return f"{sign}${abs_val:.0f}"


# ── Market Overview ──────────────────────────────────────────


async def get_market_overview(db: AsyncIOMotorDatabase) -> dict:
    """Aggregate trade_data for market overview KPIs (optimised: 1 pipeline + parallel counts)."""
    cached = _scache_get("market_overview")
    if cached:
        return cached

    latest_doc = await db.trade_data.find_one(sort=[("period_date", -1)])
    latest_year = latest_doc["period_date"].year if (latest_doc and latest_doc.get("period_date")) else datetime.now().year
    prev_year = latest_year - 1

    prev_start = datetime(prev_year, 1, 1)
    year_start = datetime(latest_year, 1, 1)
    year_end = datetime(latest_year, 12, 31, 23, 59, 59)

    # Single aggregation for all 4 trade totals + parallel counts
    trade_pipeline = [
        {"$match": {"period_date": {"$gte": prev_start, "$lte": year_end}}},
        {
            "$group": {
                "_id": {
                    "flow": "$flow",
                    "is_current": {"$gte": ["$period_date", year_start]},
                },
                "total": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
            }
        },
    ]

    rows, seg_count, comp_count, ins_count = await asyncio.gather(
        db.trade_data.aggregate(trade_pipeline).to_list(20),
        db.market_segments.count_documents({}),
        db.companies.count_documents({}),
        db.insights.count_documents({}),
    )

    export_total = import_total = prev_export = prev_import = 0.0
    for row in rows:
        flow = row["_id"]["flow"]
        is_cur = row["_id"]["is_current"]
        val = float(row["total"] or 0)
        if flow == "export":
            if is_cur:
                export_total += val
            else:
                prev_export += val
        elif flow == "import":
            if is_cur:
                import_total += val
            else:
                prev_import += val

    total_market = export_total + import_total
    prev_total = prev_export + prev_import
    growth_pct = ((total_market - prev_total) / prev_total * 100) if prev_total > 0 else None

    result = {
        "total_market_size_usd": total_market,
        "market_size_formatted": _format_value(total_market),
        "growth_pct": round(growth_pct, 1) if growth_pct is not None else None,
        "trade_balance_usd": export_total - import_total,
        "export_total_usd": export_total,
        "import_total_usd": import_total,
        "segment_count": seg_count,
        "company_count": comp_count,
        "insight_count": ins_count,
        "latest_year": latest_year,
    }
    _scache_set("market_overview", result)
    return result


# ── Segments ─────────────────────────────────────────────────


async def get_segments(db: AsyncIOMotorDatabase, axis: str | None = None) -> list[dict]:
    """Get market segments (N+1 fixed: one batch aggregation instead of one query per segment)."""
    filter_dict: dict = {}
    if axis:
        filter_dict["axis"] = axis

    segments, size_rows = await asyncio.gather(
        db.market_segments.find(filter_dict).sort("code", 1).to_list(200),
        db.market_size_series.aggregate([
            {"$sort": {"year": -1}},
            {"$group": {"_id": "$segment_code", "value_usd": {"$first": "$value_usd"}}},
        ]).to_list(500),
    )

    # Build lookup map: segment_code → latest value_usd
    size_map = {row["_id"]: row["value_usd"] for row in size_rows}

    return [
        {
            "id": str(seg["_id"]),
            "axis": seg.get("axis", ""),
            "code": seg.get("code", ""),
            "label_fr": seg.get("label_fr", ""),
            "label_en": seg.get("label_en", ""),
            "parent_code": seg.get("parent_code"),
            "description_fr": seg.get("description_fr", ""),
            "market_value": size_map.get(seg.get("code")),
        }
        for seg in segments
    ]


# ── Market Size Series ───────────────────────────────────────


async def get_market_size_series(
    db: AsyncIOMotorDatabase,
    segment_code: str | None = None,
    geography_code: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[dict]:
    """Get market size time series."""
    filter_dict: dict = {}
    if segment_code:
        filter_dict["segment_code"] = segment_code
    if geography_code:
        filter_dict["geography_code"] = geography_code
    if year_from:
        filter_dict.setdefault("year", {})["$gte"] = year_from
    if year_to:
        filter_dict.setdefault("year", {})["$lte"] = year_to

    cursor = db.market_size_series.find(filter_dict).sort("year", 1)
    docs = await cursor.to_list(500)

    return [
        {
            "year": d["year"],
            "value_usd": d.get("value_usd", 0),
            "flow": d.get("flow", "total"),
            "segment_code": d.get("segment_code", ""),
            "geography_code": d.get("geography_code", ""),
        }
        for d in docs
    ]


# ── Companies ────────────────────────────────────────────────


async def get_companies(
    db: AsyncIOMotorDatabase,
    search: str | None = None,
    country: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Get company profiles."""
    filter_dict: dict = {}
    if search:
        filter_dict["name"] = {"$regex": search, "$options": "i"}
    if country:
        filter_dict["country"] = country

    cursor = db.companies.find(filter_dict).sort("name", 1).limit(limit)
    docs = await cursor.to_list(limit)

    result = []
    for d in docs:
        # Get latest market share for this company
        share_doc = await db.market_share_series.find_one(
            {"company_name": d["name"]},
            sort=[("year", -1)],
        )
        result.append({
            "id": str(d["_id"]),
            "name": d.get("name") or "",
            "country": d.get("country") or "MA",
            "hq_city": d.get("hq_city") or "",
            "description_fr": d.get("description_fr") or "",
            "swot": d.get("swot") or {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
            "financials": d.get("financials") or {},
            "executives": d.get("executives") or [],
            "website": d.get("website") or "",
            "sector": d.get("sector") or "textile",
            "market_share_pct": share_doc["share_pct"] if share_doc else None,
        })
    return result


# ── Market Share ─────────────────────────────────────────────


async def derive_market_share_from_companies(db: AsyncIOMotorDatabase) -> int:
    """Derive market share from company revenue data and upsert into market_share_series."""
    from motor.motor_asyncio import AsyncIOMotorDatabase as _DB  # noqa: F401
    current_year = datetime.now().year

    companies_cursor = db.companies.find(
        {"financials.revenue_usd": {"$gt": 0}},
        {"name": 1, "financials": 1},
    )
    companies = await companies_cursor.to_list(200)

    if not companies:
        logger.info("derive_market_share: no companies with revenue_usd > 0")
        return 0

    total_revenue = sum(float(c.get("financials", {}).get("revenue_usd", 0) or 0) for c in companies)
    if total_revenue == 0:
        logger.info("derive_market_share: total revenue is 0")
        return 0

    ops_count = 0
    for c in companies:
        rev = float(c.get("financials", {}).get("revenue_usd", 0) or 0)
        if rev <= 0:
            continue
        share_pct = round((rev / total_revenue) * 100, 2)
        await db.market_share_series.update_one(
            {
                "company_name": c["name"],
                "segment_code": "all",
                "year": current_year,
            },
            {
                "$set": {
                    "company_name": c["name"],
                    "segment_code": "all",
                    "year": current_year,
                    "share_pct": share_pct,
                    "value_usd": rev,
                }
            },
            upsert=True,
        )
        ops_count += 1

    logger.info(f"derive_market_share: upserted {ops_count} entries for year {current_year}")
    return ops_count


async def get_market_share(
    db: AsyncIOMotorDatabase,
    segment_code: str = "all",
    year: int | None = None,
) -> dict:
    """Get market share breakdown for a segment and year."""
    if year is None:
        latest = await db.market_share_series.find_one(sort=[("year", -1)])
        year = latest["year"] if latest else datetime.now().year

    filter_dict: dict = {"year": year}
    if segment_code and segment_code != "all":
        filter_dict["segment_code"] = segment_code

    cursor = db.market_share_series.find(filter_dict).sort("share_pct", -1)
    docs = await cursor.to_list(50)

    # If collection is empty, auto-derive from company revenue data
    if not docs:
        logger.info("market_share_series empty — auto-deriving from companies")
        count = await derive_market_share_from_companies(db)
        if count > 0:
            # Re-query after population
            cursor2 = db.market_share_series.find(filter_dict).sort("share_pct", -1)
            docs = await cursor2.to_list(50)

    return {
        "year": year,
        "segment_code": segment_code,
        "entries": [
            {
                "company_name": d.get("company_name", ""),
                "share_pct": d.get("share_pct", 0),
                "value_usd": d.get("value_usd", 0),
            }
            for d in docs
        ],
    }


# ── Competitive Events ───────────────────────────────────────


async def get_competitive_events(
    db: AsyncIOMotorDatabase,
    event_type: str | None = None,
    limit: int = 30,
) -> list[dict]:
    """Get competitive events timeline."""
    filter_dict: dict = {}
    if event_type:
        filter_dict["event_type"] = event_type

    cursor = db.competitive_events.find(filter_dict).sort("event_date", -1).limit(limit)
    docs = await cursor.to_list(limit)

    return [
        {
            "id": str(d["_id"]),
            "event_type": d.get("event_type", ""),
            "company_name": d.get("company_name", ""),
            "title": d.get("title", ""),
            "description_fr": d.get("description_fr", ""),
            "event_date": d.get("event_date"),
            "source_url": d.get("source_url", ""),
            "source_name": d.get("source_name", ""),
        }
        for d in docs
    ]


# ── Insights ─────────────────────────────────────────────────


async def get_insights(
    db: AsyncIOMotorDatabase,
    category: str | None = None,
) -> list[dict]:
    """Get market insights."""
    filter_dict: dict = {}
    if category:
        filter_dict["category"] = category

    cursor = db.insights.find(filter_dict).sort("created_at", -1).limit(50)
    docs = await cursor.to_list(50)

    return [
        {
            "id": str(d["_id"]),
            "category": d.get("category", ""),
            "title": d.get("title", ""),
            "narrative_fr": d.get("narrative_fr", ""),
            "droc_type": d.get("droc_type"),
            "tags": d.get("tags", []),
            "created_at": d.get("created_at"),
        }
        for d in docs
    ]


# ── Framework Generation (LLM-based, on-demand) ─────────────


async def generate_framework(
    db: AsyncIOMotorDatabase,
    framework_type: str,
    parameters: dict | None = None,
) -> dict:
    """Generate a Porter/PESTEL/TAM analysis on demand using LLM."""
    # Check if we already have a recent result (less than 24h old)
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    existing = await db.framework_results.find_one(
        {"framework_type": framework_type, "created_at": {"$gte": cutoff}},
        sort=[("created_at", -1)],
    )
    if existing:
        return {
            "id": str(existing["_id"]),
            "framework_type": existing["framework_type"],
            "content": existing["content"],
            "created_at": existing.get("created_at"),
        }

    # Gather context data from trade_data
    trade_summary = await _gather_trade_summary(db)

    # Generate with OpenAI
    content = _generate_framework_llm(framework_type, trade_summary, parameters)

    # Store result
    from app.models.market_research import new_framework_result_doc
    doc = new_framework_result_doc(framework_type, content, parameters)
    await db.framework_results.insert_one(doc)

    return {
        "id": doc["_id"],
        "framework_type": framework_type,
        "content": content,
        "created_at": doc["created_at"],
    }


async def _gather_trade_summary(db: AsyncIOMotorDatabase) -> dict:
    """Gather summary data for framework generation context."""
    # Trade totals
    pipeline = [
        {"$group": {
            "_id": "$flow",
            "total": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
        }},
    ]
    totals = {r["_id"]: r["total"] for r in await db.trade_data.aggregate(pipeline).to_list(10)}

    # Top partners
    partner_pipeline = [
        {"$match": {"partner_code": {"$nin": ["0", "MA", "504"]}}},
        {"$group": {"_id": "$partner_name", "value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}}}},
        {"$sort": {"value": -1}},
        {"$limit": 10},
    ]
    top_partners = [
        {"name": r["_id"], "value": r["value"]}
        for r in await db.trade_data.aggregate(partner_pipeline).to_list(10)
    ]

    # HS chapter breakdown
    hs_pipeline = [
        {"$group": {"_id": {"$substr": ["$hs_code", 0, 2]}, "value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}}}},
        {"$sort": {"value": -1}},
    ]
    hs_breakdown = [
        {"chapter": r["_id"], "value": r["value"]}
        for r in await db.trade_data.aggregate(hs_pipeline).to_list(20)
    ]

    # Companies
    companies = await db.companies.find({}, {"name": 1, "description_fr": 1}).to_list(20)

    # Recent news
    news_cursor = db.news_articles.find(
        {}, {"title": 1, "category": 1}
    ).sort("published_at", -1).limit(15)
    news_list = await news_cursor.to_list(15)

    return {
        "export_total_usd": totals.get("export", 0),
        "import_total_usd": totals.get("import", 0),
        "top_partners": top_partners,
        "hs_breakdown": hs_breakdown,
        "companies": [{"name": c.get("name", ""), "description": c.get("description_fr", "")} for c in companies],
        "recent_news_titles": [n.get("title", "") for n in news_list],
    }


def _generate_framework_llm(framework_type: str, context: dict, parameters: dict | None = None) -> dict:
    """Call OpenAI to generate a framework analysis."""
    if not settings.OPENAI_API_KEY:
        return _fallback_framework(framework_type)

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    prompts = {
        "porter": {
            "name": "Analyse des 5 Forces de Porter",
            "structure": '{"rivalry": "...", "new_entrants": "...", "substitutes": "...", "buyer_power": "...", "supplier_power": "...", "summary": "..."}',
            "instruction": "Analyse les 5 forces de Porter pour le secteur textile marocain. Pour chaque force, donne un score (faible/moyen/fort) et une explication detaillee.",
        },
        "pestel": {
            "name": "Analyse PESTEL",
            "structure": '{"political": "...", "economic": "...", "social": "...", "technological": "...", "environmental": "...", "legal": "...", "summary": "..."}',
            "instruction": "Realise une analyse PESTEL du secteur textile et habillement au Maroc. Pour chaque dimension, fournis 2-3 facteurs cles avec leur impact.",
        },
        "tam_sam_som": {
            "name": "Analyse TAM/SAM/SOM",
            "structure": '{"tam": {"value_usd": 0, "description": "..."}, "sam": {"value_usd": 0, "description": "..."}, "som": {"value_usd": 0, "description": "..."}, "methodology": "...", "summary": "..."}',
            "instruction": "Estime le TAM (marche total adressable), SAM (marche disponible exploitable), et SOM (marche obtenable) pour le textile marocain. Utilise les donnees fournies pour des estimations realistes.",
        },
    }

    prompt_info = prompts.get(framework_type, prompts["porter"])

    system = (
        "Tu es un consultant senior en strategie specialise dans le secteur textile international. "
        "Tu rediges en francais. Utilise UNIQUEMENT les donnees fournies pour tes analyses. "
        "Retourne un objet JSON valide avec la structure demandee. "
        "Ne genere JAMAIS de chiffres inventes — utilise les donnees fournies ou indique 'estimation basee sur les donnees disponibles'."
    )

    data_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)
    user_prompt = f"""{prompt_info['instruction']}

Donnees du secteur textile marocain:
{data_str}

Retourne un JSON avec cette structure:
{prompt_info['structure']}

IMPORTANT: Retourne UNIQUEMENT du JSON valide, sans markdown."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2000,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        content_str = response.choices[0].message.content or "{}"
        return json.loads(content_str)
    except Exception as e:
        logger.error(f"Framework LLM generation failed: {e}")
        return _fallback_framework(framework_type)


def _fallback_framework(framework_type: str) -> dict:
    """Return a placeholder when LLM is unavailable."""
    if framework_type == "porter":
        return {
            "rivalry": "Analyse non disponible — cle API requise",
            "new_entrants": "",
            "substitutes": "",
            "buyer_power": "",
            "supplier_power": "",
            "summary": "Veuillez configurer une cle API OpenAI pour generer cette analyse.",
        }
    elif framework_type == "pestel":
        return {
            "political": "",
            "economic": "",
            "social": "",
            "technological": "",
            "environmental": "",
            "legal": "",
            "summary": "Veuillez configurer une cle API OpenAI pour generer cette analyse.",
        }
    else:  # tam_sam_som
        return {
            "tam": {"value_usd": 0, "description": "Non disponible"},
            "sam": {"value_usd": 0, "description": "Non disponible"},
            "som": {"value_usd": 0, "description": "Non disponible"},
            "methodology": "",
            "summary": "Veuillez configurer une cle API OpenAI pour generer cette analyse.",
        }
