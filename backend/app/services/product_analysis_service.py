"""Deep product analysis service — aggregates trade data + market intelligence + LLM frameworks."""
import asyncio
import json
import logging
import time
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)

# ── 30-minute in-memory TTL cache ────────────────────────────────────────────
_cache: dict = {}
_CACHE_TTL = 1800  # 30 minutes


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and time.time() < entry["expires"]:
        return entry["data"]
    _cache.pop(key, None)
    return None


def _cache_set(key: str, data: dict):
    _cache[key] = {"data": data, "expires": time.time() + _CACHE_TTL}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt(val: float) -> str:
    if val >= 1e9:
        return f"${val / 1e9:.1f}B"
    if val >= 1e6:
        return f"${val / 1e6:.1f}M"
    if val >= 1e3:
        return f"${val / 1e3:.0f}K"
    return f"${val:.0f}"


# ── MongoDB aggregations ──────────────────────────────────────────────────────

async def _get_flow_total(db: AsyncIOMotorDatabase, hs_code: str, flow: str, year: int) -> float:
    pipeline = [
        {"$match": {
            "hs_code": {"$regex": f"^{hs_code}"},
            "flow": flow,
            "period_date": {"$gte": datetime(year, 1, 1), "$lte": datetime(year, 12, 31)},
        }},
        {"$group": {"_id": None, "value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}}}},
    ]
    rows = await db.trade_data.aggregate(pipeline).to_list(1)
    return float(rows[0]["value"]) if rows else 0.0


async def _get_top_partners(db: AsyncIOMotorDatabase, hs_code: str, year: int, limit: int = 10) -> list[dict]:
    pipeline = [
        {"$match": {
            "hs_code": {"$regex": f"^{hs_code}"},
            "partner_code": {"$ne": "0"},
            "period_date": {"$gte": datetime(year, 1, 1), "$lte": datetime(year, 12, 31)},
        }},
        {"$group": {
            "_id": "$partner_name",
            "value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
        }},
        {"$sort": {"value": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "label": "$_id", "value": 1}},
    ]
    return await db.trade_data.aggregate(pipeline).to_list(limit)


async def _get_top_partners_by_flow(db: AsyncIOMotorDatabase, hs_code: str, year: int, flow: str, limit: int = 10) -> list[dict]:
    pipeline = [
        {"$match": {
            "hs_code": {"$regex": f"^{hs_code}"},
            "flow": flow,
            "partner_code": {"$ne": "0"},
            "period_date": {"$gte": datetime(year, 1, 1), "$lte": datetime(year, 12, 31)},
        }},
        {"$group": {
            "_id": "$partner_name",
            "value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
        }},
        {"$sort": {"value": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "label": "$_id", "value": 1}},
    ]
    return await db.trade_data.aggregate(pipeline).to_list(limit)


async def _get_trend(db: AsyncIOMotorDatabase, hs_code: str, num_years: int = 5, ref_year: int | None = None) -> list[dict]:
    end_year = ref_year or datetime.now().year
    start_year = end_year - num_years + 1
    pipeline = [
        {"$match": {
            "hs_code": {"$regex": f"^{hs_code}"},
            "period_date": {"$gte": datetime(start_year, 1, 1), "$lte": datetime(end_year, 12, 31)},
        }},
        {"$group": {
            "_id": {"year": {"$year": "$period_date"}, "flow": "$flow"},
            "value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
        }},
        {"$sort": {"_id.year": 1}},
    ]
    rows = await db.trade_data.aggregate(pipeline).to_list(num_years * 4)
    by_year: dict[int, dict] = {}
    for r in rows:
        y = r["_id"]["year"]
        f = r["_id"]["flow"]
        if y not in by_year:
            by_year[y] = {"year": y, "export_usd": 0.0, "import_usd": 0.0}
        if f == "export":
            by_year[y]["export_usd"] = float(r["value"])
        elif f == "import":
            by_year[y]["import_usd"] = float(r["value"])
    return sorted(by_year.values(), key=lambda x: x["year"])


async def _get_hs_description(db: AsyncIOMotorDatabase, hs_code: str) -> str:
    doc = await db.trade_data.find_one(
        {"hs_code": {"$regex": f"^{hs_code}"}, "hs_description": {"$exists": True, "$ne": None, "$ne": ""}},
        {"hs_description": 1},
    )
    return doc.get("hs_description", "") if doc else ""


async def _get_companies_enriched(db: AsyncIOMotorDatabase, limit: int = 20) -> list[dict]:
    try:
        companies = await db.companies.find(
            {}, {"name": 1, "description_fr": 1, "country": 1, "hq_city": 1, "swot": 1, "financials": 1, "website": 1, "sector": 1}
        ).to_list(limit)
        results = []
        for c in companies:
            share_doc = await db.market_share_series.find_one(
                {"company_name": c.get("name")}, {"share_pct": 1, "value_usd": 1}, sort=[("year", -1)]
            )
            entry = {
                "name": c.get("name", ""),
                "description": c.get("description_fr", ""),
                "country": c.get("country", ""),
                "city": c.get("hq_city", ""),
                "website": c.get("website", ""),
                "sector": c.get("sector", ""),
                "market_share_pct": float(share_doc["share_pct"]) if share_doc and share_doc.get("share_pct") else None,
                "revenue_usd": None,
            }
            fin = c.get("financials") or {}
            if isinstance(fin, dict):
                entry["revenue_usd"] = fin.get("revenue_usd")
            results.append(entry)
        return results
    except Exception:
        return []


async def _get_competitive_events(db: AsyncIOMotorDatabase, limit: int = 15) -> list[dict]:
    try:
        events = await db.competitive_events.find(
            {}, {"event_type": 1, "company_name": 1, "title": 1, "description_fr": 1, "event_date": 1, "source_url": 1, "source_name": 1}
        ).sort("event_date", -1).to_list(limit)
        return [{
            "event_type": e.get("event_type", ""), "company": e.get("company_name", ""),
            "title": e.get("title", ""), "description": e.get("description_fr", ""),
            "date": str(e.get("event_date", ""))[:10] if e.get("event_date") else "",
            "source_url": e.get("source_url", ""), "source_name": e.get("source_name", ""),
        } for e in events]
    except Exception:
        return []


async def _get_news_enriched(db: AsyncIOMotorDatabase, limit: int = 20) -> list[dict]:
    try:
        articles = await db.news_articles.find(
            {}, {"title": 1, "summary": 1, "source_url": 1, "source_name": 1, "category": 1, "tags": 1, "published_at": 1}
        ).sort("published_at", -1).to_list(limit)
        return [{
            "title": a.get("title", ""), "summary": (a.get("summary") or "")[:200],
            "source_url": a.get("source_url", ""), "source_name": a.get("source_name", ""),
            "category": a.get("category", ""), "tags": a.get("tags", []),
            "published_at": str(a.get("published_at", "")) if a.get("published_at") else "",
        } for a in articles]
    except Exception:
        return []


# ── LLM analysis ─────────────────────────────────────────────────────────────

def _generate_product_llm(context: dict) -> dict:
    if not settings.OPENAI_API_KEY:
        return _fallback_analysis(context)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        hs = context.get("hs_code", "")
        desc = context.get("hs_description", "produit textile")
        year = context.get("year", "")

        system = (
            "Tu es un consultant senior en stratégie commerciale spécialisé dans le secteur textile international. "
            "Tu rédiges UNIQUEMENT en français. Tu retournes TOUJOURS du JSON valide avec la structure exacte demandée. "
            "Ne génère JAMAIS de chiffres inventés — utilise les données fournies ou indique 'estimation'. "
            "Sois exhaustif, analytique et précis dans chaque section."
        )

        structure = """{
  "pestel": {"political":"...","economic":"...","social":"...","technological":"...","environmental":"...","legal":"...","summary":"..."},
  "tam_sam_som": {"tam":{"value_usd":0,"description":"..."},"sam":{"value_usd":0,"description":"..."},"som":{"value_usd":0,"description":"..."},"methodology":"...","summary":"..."},
  "porter": {"rivalry":"...","new_entrants":"...","substitutes":"...","buyer_power":"...","supplier_power":"...","summary":"..."},
  "bcg": {"position":"star|cash_cow|question_mark|dog","x_market_share":0.0,"y_market_growth":0.0,"justification":"..."},
  "market_segmentation": {"segments":[{"name":"...","share_pct":0,"size_usd":0,"growth":"...","description":"..."}],"summary":"..."},
  "leader_companies": [{"name":"...","country":"...","market_share_pct":0,"strengths":"...","description":"..."}],
  "trend_probability": {"upward_pct":0,"justification":"..."},
  "recommendations": ["rec1","rec2","rec3","rec4","rec5"],
  "strategic_projection": "..."
}"""

        data_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)
        user_msg = f"""Analyse approfondie du produit textile marocain : HS {hs} — {desc} (année {year}).

Données :
{data_str}

Retourne un JSON avec cette structure exacte :
{structure}

IMPORTANT :
- JSON valide uniquement, sans markdown.
- market_segmentation : 3-6 segments pertinents.
- leader_companies : 5-8 entreprises leaders mondiales et marocaines.
- trend_probability.upward_pct : pourcentage 0-100 basé sur les données.
- Recommandations spécifiques et actionnables pour le Maroc.
- Projection stratégique sur 3-5 ans avec jalons concrets."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user_msg}],
            max_tokens=4000,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        content_str = response.choices[0].message.content or "{}"
        return json.loads(content_str)
    except Exception as e:
        logger.error(f"Product analysis LLM failed: {e}")
        return _fallback_analysis(context)


def _fallback_analysis(context: dict) -> dict:
    exp = context.get("export_total_usd", 0)
    imp = context.get("import_total_usd", 0)
    trend = context.get("trend_pct", 0)
    companies_ctx = context.get("companies", [])
    upward_pct = max(5, min(95, int(50 + trend))) if trend else 50

    return {
        "pestel": {
            "political": "Accords de libre-échange (UE, USA, Afrique) favorables. Politiques industrielles de soutien au textile.",
            "economic": f"Exports : {_fmt(exp)}, Imports : {_fmt(imp)}. Pilier économique marocain.",
            "social": "Main-d'œuvre qualifiée, coûts compétitifs. Tendance vers la mode éthique.",
            "technological": "Adoption progressive de l'industrie 4.0 et digitalisation.",
            "environmental": "Pression durabilité croissante. EU Green Deal impactant.",
            "legal": "Normes CE, certifications OEKO-TEX, règles d'origine.",
            "summary": "Contexte globalement favorable avec opportunités proximité UE et défis durabilité.",
        },
        "tam_sam_som": {
            "tam": {"value_usd": max(exp * 12, 1e9), "description": "Marché mondial textile/habillement"},
            "sam": {"value_usd": max(exp * 5, 5e8), "description": "Marché accessible (UE + Afrique + MENA)"},
            "som": {"value_usd": max(exp * 1.5, exp), "description": "Part obtenable par le Maroc"},
            "methodology": "Estimation basée sur données d'export et ratios sectoriels.",
            "summary": "Potentiel de croissance significatif par rapport aux exports actuels.",
        },
        "porter": {
            "rivalry": "Forte — concurrence intense (Turquie, Tunisie, Bangladesh, Chine).",
            "new_entrants": "Modérée — barrières investissements et certifications.",
            "substitutes": "Faible à modérée — synthétiques progressent mais savoir-faire marocain différenciant.",
            "buyer_power": "Fort — grands distributeurs européens exercent pression prix.",
            "supplier_power": "Modéré — dépendance importations matières premières.",
            "summary": "Environnement exigeant mais avantages stratégiques marocains (proximité, accords).",
        },
        "bcg": {
            "position": "star" if trend > 5 else "question_mark" if trend > 0 else "cash_cow" if exp > imp else "dog",
            "x_market_share": min(0.8, max(0.1, exp / max(imp * 5, 1))),
            "y_market_growth": min(0.8, max(0.05, abs(trend) / 100)),
            "justification": f"Basé sur tendance ({trend:+.1f}%) et ratio export/import.",
        },
        "market_segmentation": {
            "segments": [
                {"name": "Prêt-à-porter", "share_pct": 45, "size_usd": exp * 0.45, "growth": "+3-5%/an", "description": "Fast fashion, sous-traitance"},
                {"name": "Textiles techniques", "share_pct": 15, "size_usd": exp * 0.15, "growth": "+7-9%/an", "description": "Usage industriel, médical, automobile"},
                {"name": "Textiles maison", "share_pct": 12, "size_usd": exp * 0.12, "growth": "+2-3%/an", "description": "Linge de maison, tapis"},
                {"name": "Sous-traitance", "share_pct": 20, "size_usd": exp * 0.20, "growth": "+4-6%/an", "description": "Production pour marques internationales"},
                {"name": "Mode durable", "share_pct": 8, "size_usd": exp * 0.08, "growth": "+12-15%/an", "description": "Éco-responsable, forte croissance"},
            ],
            "summary": "Prêt-à-porter domine mais textiles techniques et mode durable offrent meilleures perspectives.",
        },
        "leader_companies": [
            {"name": c.get("name", ""), "country": c.get("country", "MA"), "market_share_pct": c.get("market_share_pct") or round(100 / max(len(companies_ctx), 1), 1), "strengths": c.get("description", "")[:100], "description": c.get("description", "")}
            for c in companies_ctx[:6]
        ] if companies_ctx else [
            {"name": "Fruit of the Loom Morocco", "country": "MA", "market_share_pct": 8, "strengths": "Capacité de production, réseau international", "description": "Grand producteur vêtements"},
        ],
        "trend_probability": {"upward_pct": upward_pct, "justification": f"Basé sur tendance récente ({trend:+.1f}%) et conditions de marché."},
        "recommendations": [
            "Montée en gamme vers textiles techniques et mode durable.",
            "Digitalisation chaîne de valeur (ERP, traçabilité, e-commerce B2B).",
            "Diversification marchés : Afrique subsaharienne et Moyen-Orient.",
            "Certifications durabilité (GOTS, OEKO-TEX) pour exigences UE.",
            "Partenariats stratégiques avec marques internationales.",
        ],
        "strategic_projection": f"Sur 3-5 ans, trajectoire de {'croissance' if trend > 0 else 'stabilisation'}. Axes : montée en gamme, diversification géographique, pratiques durables (Green Deal UE).",
    }


# ── Main orchestrator ─────────────────────────────────────────────────────────

async def run_deep_analysis(db: AsyncIOMotorDatabase, hs_code: str, year: int) -> dict:
    hs_code = hs_code.strip()
    cache_key = f"deep_{hs_code}_{year}"

    cached = _cache_get(cache_key)
    if cached:
        logger.info(f"Deep analysis cache hit: {cache_key}")
        return cached

    logger.info(f"Running deep analysis: hs={hs_code} year={year}")

    # ── Step 1: Parallel data gathering ───────────────────────────────────────
    (
        export_total, import_total, top_partners, export_partners, import_partners,
        trend_data, hs_description, companies_raw, news_raw, events_raw,
    ) = await asyncio.gather(
        _get_flow_total(db, hs_code, "export", year),
        _get_flow_total(db, hs_code, "import", year),
        _get_top_partners(db, hs_code, year, 10),
        _get_top_partners_by_flow(db, hs_code, year, "export", 10),
        _get_top_partners_by_flow(db, hs_code, year, "import", 10),
        _get_trend(db, hs_code, 5, year),
        _get_hs_description(db, hs_code),
        _get_companies_enriched(db, 20),
        _get_news_enriched(db, 20),
        _get_competitive_events(db, 15),
    )

    # ── Step 2: Trend indicator ───────────────────────────────────────────────
    trend_pct = 0.0
    trend_direction = "stable"
    if len(trend_data) >= 2:
        prev_exp = trend_data[-2].get("export_usd", 0)
        curr_exp = trend_data[-1].get("export_usd", 0)
        if prev_exp > 0:
            trend_pct = round(((curr_exp - prev_exp) / prev_exp) * 100, 1)
            trend_direction = "hausse" if trend_pct > 0 else "baisse"

    # ── Step 3: Build context for LLM ─────────────────────────────────────────
    product_context = {
        "hs_code": hs_code,
        "hs_description": hs_description or f"Produit textile HS {hs_code}",
        "year": year,
        "export_total_usd": export_total,
        "import_total_usd": import_total,
        "trade_balance_usd": export_total - import_total,
        "export_formatted": _fmt(export_total),
        "import_formatted": _fmt(import_total),
        "top_partners": [{"partner": p["label"], "value_usd": p["value"]} for p in top_partners[:5]],
        "top_export_destinations": [{"partner": p["label"], "value_usd": p["value"]} for p in export_partners[:5]],
        "top_import_sources": [{"partner": p["label"], "value_usd": p["value"]} for p in import_partners[:5]],
        "trend_data": trend_data,
        "trend_pct": trend_pct,
        "trend_direction": trend_direction,
        "companies": [{"name": c["name"], "description": c["description"], "country": c["country"]} for c in companies_raw[:12]],
        "competitive_events": [{"title": e["title"], "company": e["company"], "type": e["event_type"]} for e in events_raw[:8]],
        "recent_news": [{"title": n["title"], "category": n["category"]} for n in news_raw[:10]],
    }

    # ── Step 4: LLM frameworks ────────────────────────────────────────────────
    loop = asyncio.get_event_loop()
    frameworks = await loop.run_in_executor(None, _generate_product_llm, product_context)

    # ── Step 5: Build result ──────────────────────────────────────────────────
    result = {
        "hs_code": hs_code,
        "hs_description": hs_description or f"Produit textile HS {hs_code}",
        "year": year,
        "export_total_usd": export_total,
        "import_total_usd": import_total,
        "trade_balance_usd": export_total - import_total,
        "export_formatted": _fmt(export_total),
        "import_formatted": _fmt(import_total),
        "trade_trend": trend_data,
        "trend_pct": trend_pct,
        "trend_direction": trend_direction,
        "top_partners": top_partners,
        "export_partners": export_partners,
        "import_partners": import_partners,
        "frameworks": frameworks,
        "companies": [{
            "name": c.get("name", ""), "description": c.get("description", ""),
            "country": c.get("country", ""), "city": c.get("city", ""),
            "website": c.get("website", ""), "market_share_pct": c.get("market_share_pct"),
            "revenue_usd": c.get("revenue_usd"),
        } for c in companies_raw],
        "recent_news": [{
            "title": n.get("title", ""), "summary": n.get("summary", ""),
            "source_url": n.get("source_url", ""), "source_name": n.get("source_name", ""),
            "category": n.get("category", ""), "tags": n.get("tags", []),
            "published_at": n.get("published_at", ""),
        } for n in news_raw],
        "competitive_events": events_raw,
    }

    _cache_set(cache_key, result)
    return result
