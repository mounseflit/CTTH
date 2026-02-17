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


async def _sum_trade_value(db, flow: str, date_gte: datetime, date_lte: datetime | None = None) -> float:
    """Aggregate total trade value for a given flow and date range."""
    match: dict = {"flow": flow, "period_date": {"$gte": date_gte}}
    if date_lte:
        match["period_date"]["$lte"] = date_lte

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": None,
                "total": {
                    "$sum": {
                        "$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]
                    }
                },
            }
        },
    ]
    result = await db.trade_data.aggregate(pipeline).to_list(1)
    return float(result[0]["total"]) if result else 0.0


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # Use the most recent year that actually has data, not the calendar year
    latest_doc = await db.trade_data.find_one(
        sort=[("period_date", -1)]
    )
    if latest_doc and latest_doc.get("period_date"):
        current_year = latest_doc["period_date"].year
    else:
        current_year = date.today().year
    prev_year = current_year - 1
    year_start = datetime(current_year, 1, 1)
    prev_year_start = datetime(prev_year, 1, 1)
    prev_year_end = datetime(prev_year, 12, 31)

    # KPI: Export/Import totals
    export_total = await _sum_trade_value(db, "export", year_start)
    prev_export_total = await _sum_trade_value(db, "export", prev_year_start, prev_year_end)
    import_total = await _sum_trade_value(db, "import", year_start)
    prev_import_total = await _sum_trade_value(db, "import", prev_year_start, prev_year_end)

    export_change = (
        ((export_total - prev_export_total) / prev_export_total * 100)
        if prev_export_total > 0
        else 0
    )
    import_change = (
        ((import_total - prev_import_total) / prev_import_total * 100)
        if prev_import_total > 0
        else 0
    )
    balance = export_total - import_total

    # KPI: News count (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    news_count = await db.news_articles.count_documents(
        {"created_at": {"$gte": thirty_days_ago}}
    )

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
            value=format_value(balance),
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

    # Trend data: group by period_date and flow
    three_years_ago = datetime(current_year - 3, 1, 1)
    trend_pipeline = [
        {"$match": {"period_date": {"$gte": three_years_ago}}},
        {
            "$group": {
                "_id": {
                    "period": {
                        "$dateToString": {"format": "%Y-%m", "date": "$period_date"}
                    },
                    "flow": "$flow",
                },
                "total": {
                    "$sum": {
                        "$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]
                    }
                },
            }
        },
        {"$sort": {"_id.period": 1}},
    ]

    trend_results = await db.trade_data.aggregate(trend_pipeline).to_list(500)
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

    # Recent news
    news_cursor = (
        db.news_articles.find({}, {"title": 1, "category": 1, "source_name": 1, "published_at": 1})
        .sort("published_at", -1)
        .limit(10)
    )
    recent_news = [
        RecentNewsItem(
            id=str(a.get("_id", "")),
            title=a.get("title", ""),
            category=a.get("category"),
            source_name=a.get("source_name"),
            published_at=a.get("published_at"),
        )
        for a in await news_cursor.to_list(10)
    ]

    # Top partners (exclude world=0, Morocco=MA/504)
    partners_pipeline = [
        {"$match": {
            "partner_code": {"$nin": ["0", "MA", "504"]},
            "period_date": {"$gte": year_start},
        }},
        {
            "$group": {
                "_id": "$partner_name",
                "value": {
                    "$sum": {
                        "$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]
                    }
                },
            }
        },
        {"$sort": {"value": -1}},
        {"$limit": 5},
        {"$project": {"_id": 0, "partner_name": "$_id", "value": 1}},
    ]
    top_partners = await db.trade_data.aggregate(partners_pipeline).to_list(5)

    # HS breakdown (exclude TOTAL/aggregate codes)
    hs_pipeline = [
        {"$match": {
            "period_date": {"$gte": year_start},
            "hs_code": {"$nin": ["TOTAL", "SITC_TOTAL", None, ""]},
        }},
        {
            "$group": {
                "_id": {"$substr": ["$hs_code", 0, 2]},
                "value": {
                    "$sum": {
                        "$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]
                    }
                },
            }
        },
        {"$sort": {"value": -1}},
        {"$project": {"_id": 0, "chapter": "$_id", "value": 1}},
    ]
    hs_breakdown = await db.trade_data.aggregate(hs_pipeline).to_list(100)

    return DashboardResponse(
        kpi_cards=kpi_cards,
        trend_data=trend_data,
        recent_news=recent_news,
        top_partners=top_partners,
        hs_breakdown=hs_breakdown,
    )
