from datetime import date

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.trade import TradeDataResponse, TradePaginatedResponse
from app.services.trade_service import (
    get_aggregated_data,
    get_hs_breakdown,
    get_top_partners,
    get_trade_data,
)

router = APIRouter()


@router.get("/data", response_model=TradePaginatedResponse)
async def get_trade_data_endpoint(
    hs_codes: str | None = Query(None, description="Comma-separated HS codes"),
    partners: str | None = Query(None, description="Comma-separated partner codes"),
    flow: str | None = Query(None, description="import, export, or all"),
    source: str | None = Query(None, description="eurostat, comtrade, or all"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    frequency: str | None = Query(None, description="A or M"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    hs_list = hs_codes.split(",") if hs_codes else None
    partner_list = partners.split(",") if partners else None

    data, total = await get_trade_data(
        db,
        hs_codes=hs_list,
        partners=partner_list,
        flow=flow,
        source=source,
        date_from=date_from,
        date_to=date_to,
        frequency=frequency,
        page=page,
        per_page=per_page,
    )

    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    return TradePaginatedResponse(
        data=[
            TradeDataResponse(
                id=i + 1,  # Auto-increment style ID for frontend
                period_date=str(d.get("period_date", ""))[:10],
                source=d.get("source", ""),
                reporter_code=d.get("reporter_code", ""),
                reporter_name=d.get("reporter_name"),
                partner_code=d.get("partner_code", ""),
                partner_name=d.get("partner_name"),
                hs_code=d.get("hs_code", ""),
                hs_description=d.get("hs_description"),
                flow=d.get("flow", ""),
                value_usd=d.get("value_usd"),
                value_eur=d.get("value_eur"),
                weight_kg=d.get("weight_kg"),
                quantity=d.get("quantity"),
                frequency=d.get("frequency", "A"),
            )
            for i, d in enumerate(data)
        ],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/aggregated")
async def get_aggregated(
    group_by: str = Query("partner", description="partner, hs_code, period, flow"),
    flow: str | None = Query(None),
    source: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await get_aggregated_data(db, group_by, flow, source, date_from, date_to)


@router.get("/top-partners")
async def get_top_partners_endpoint(
    flow: str | None = Query(None),
    year: int | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await get_top_partners(db, flow, year, limit)


@router.get("/hs-breakdown")
async def get_hs_breakdown_endpoint(
    flow: str | None = Query(None),
    year: int | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await get_hs_breakdown(db, flow, year)
