import asyncio
import time
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.dashboard import (
    DashboardResponse,
    KPICard,
    RecentNewsItem,
    TrendDataPoint,
)

router = APIRouter()

# ── Simple in-memory TTL cache (5 min) ───────────────────────
_dashboard_cache: dict = {}
_CACHE_TTL = 300  # seconds


def _cache_get(key: str):
    entry = _dashboard_cache.get(key)
    if entry and (time.monotonic() - entry["ts"]) < _CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data):
    _dashboard_cache[key] = {"ts": time.monotonic(), "data": data}


# ── Helpers ───────────────────────────────────────────────────

def format_value(val: float | None) -> str:
    if val is None or val == 0:
        return "$0"
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1_000_000_000:
        return f"{sign}${abs_val / 1_000_000_000:.1f}B"
    if abs_val >= 1_000_000:
        return f"{sign}${abs_val / 1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"{sign}${abs_val / 1_000:.1f}K"
    return f"{sign}${abs_val:.0f}"


async def _get_trade_kpis(db, current_year: int, prev_year: int) -> dict:
    """
    Single aggregation that computes export & import totals for
    current_year AND prev_year in one round-trip (was 4 separate pipelines).
    """
    prev_start = datetime(prev_year, 1, 1)
    year_start = datetime(current_year, 1, 1)
    year_end = datetime(current_year, 12, 31, 23, 59, 59)

    pipeline = [
        {"$match": {"period_date": {"$gte": prev_start, "$lte": year_end}}},
        {
            "$group": {
                "_id": {
                    "flow": "$flow",
                    "is_current": {"$gte": ["$period_date", year_start]},
                },
                "total": {
                    "$sum": {
                        "$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]
                    }
                },
            }
        },
    ]
    rows = await db.trade_data.aggregate(pipeline).to_list(20)

    result = {
        "export_cur": 0.0, "export_prev": 0.0,
        "import_cur": 0.0, "import_prev": 0.0,
    }
    for row in rows:
        flow = row["_id"]["flow"]
        is_cur = row["_id"]["is_current"]
        val = float(row["total"] or 0)
        if flow == "export":
            if is_cur:
                result["export_cur"] += val
            else:
                result["export_prev"] += val
        elif flow == "import":
            if is_cur:
                result["import_cur"] += val
            else:
                result["import_prev"] += val
    return result


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    cache_key = "dashboard_v1"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    # Determine latest year with data
    latest_doc = await db.trade_data.find_one(sort=[("period_date", -1)])
    if latest_doc and latest_doc.get("period_date"):
        current_year = latest_doc["period_date"].year
    else:
        current_year = date.today().year
    prev_year = current_year - 1
    year_start = datetime(current_year, 1, 1)
    three_years_ago = datetime(current_year - 3, 1, 1)

    # Run ALL heavy queries in parallel with asyncio.gather
    (
        trade_kpis,
        news_count,
        trend_results,
        recent_news_docs,
        top_partners,
        hs_breakdown,
    ) = await asyncio.gather(
        _get_trade_kpis(db, current_year, prev_year),
        db.news_articles.count_documents(
            {"created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)}}
        ),
        db.trade_data.aggregate([
            {"$match": {"period_date": {"$gte": three_years_ago}}},
            {
                "$group": {
                    "_id": {
                        "period": {"$dateToString": {"format": "%Y-%m", "date": "$period_date"}},
                        "flow": "$flow",
                    },
                    "total": {
                        "$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}
                    },
                }
            },
            {"$sort": {"_id.period": 1}},
        ]).to_list(500),
        db.news_articles.find(
            {},
            {"title": 1, "category": 1, "source_name": 1, "published_at": 1, "source_url": 1},
        ).sort("published_at", -1).limit(10).to_list(10),
        db.trade_data.aggregate([
            {"$match": {
                "partner_code": {"$nin": ["0", "MA", "504"]},
                "period_date": {"$gte": year_start},
            }},
            {"$group": {
                "_id": "$partner_name",
                "value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
            }},
            {"$sort": {"value": -1}},
            {"$limit": 5},
            {"$project": {"_id": 0, "partner_name": "$_id", "value": 1}},
        ]).to_list(5),
        db.trade_data.aggregate([
            {"$match": {
                "period_date": {"$gte": year_start},
                "hs_code": {"$nin": ["TOTAL", "SITC_TOTAL", None, ""]},
            }},
            {"$group": {
                "_id": {"$substr": ["$hs_code", 0, 2]},
                "value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
            }},
            {"$sort": {"value": -1}},
            {"$project": {"_id": 0, "chapter": "$_id", "value": 1}},
        ]).to_list(100),
    )

    # Build KPI cards
    export_total = trade_kpis["export_cur"]
    prev_export = trade_kpis["export_prev"]
    import_total = trade_kpis["import_cur"]
    prev_import = trade_kpis["import_prev"]

    export_change = ((export_total - prev_export) / prev_export * 100) if prev_export > 0 else 0
    import_change = ((import_total - prev_import) / prev_import * 100) if prev_import > 0 else 0

    kpi_cards = [
        KPICard(
            label="Exportations Textiles",
            value=format_value(export_total),
            change_pct=round(export_change, 1),
            period=f"vs. {prev_year}",
            icon="trending-up",
        ),
        KPICard(
            label="Importations Textiles",
            value=format_value(import_total),
            change_pct=round(import_change, 1),
            period=f"vs. {prev_year}",
            icon="trending-down",
        ),
        KPICard(
            label="Balance Commerciale",
            value=format_value(export_total - import_total),
            period=str(current_year),
            icon="scale",
        ),
        KPICard(
            label="Alertes & Actualites",
            value=str(news_count),
            period="30 derniers jours",
            icon="bell",
        ),
    ]

    # Build trend data
    trend_map: dict[str, dict] = {}
    for row in trend_results:
        period = row["_id"]["period"]
        flow = row["_id"]["flow"]
        if period not in trend_map:
            trend_map[period] = {"period": period, "exports": 0, "imports": 0}
        if flow == "export":
            trend_map[period]["exports"] += float(row["total"] or 0)
        else:
            trend_map[period]["imports"] += float(row["total"] or 0)

    trend_data = [
        TrendDataPoint(**v)
        for v in sorted(trend_map.values(), key=lambda x: x["period"])
    ]

    recent_news = [
        RecentNewsItem(
            id=str(a.get("_id", "")),
            title=a.get("title", ""),
            category=a.get("category"),
            source_name=a.get("source_name"),
            published_at=a.get("published_at"),
            source_url=a.get("source_url"),
        )
        for a in recent_news_docs
    ]

    response = DashboardResponse(
        kpi_cards=kpi_cards,
        trend_data=trend_data,
        recent_news=recent_news,
        top_partners=top_partners,
        hs_breakdown=hs_breakdown,
    )
    _cache_set(cache_key, response)
    return response
