"""Market research API routes."""
import asyncio

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.market_research import (
    CompanyResponse,
    CompetitiveEventResponse,
    FrameworkRequest,
    FrameworkResponse,
    InsightResponse,
    MarketOverviewResponse,
    MarketShareResponse,
    MarketSizeSeriesResponse,
    SegmentResponse,
)
from app.services.market_research_service import (
    generate_framework,
    get_companies,
    get_competitive_events,
    get_insights,
    get_market_overview,
    get_market_share,
    get_market_size_series,
    get_segments,
)

router = APIRouter()


@router.get("/overview", response_model=MarketOverviewResponse)
async def overview_endpoint(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    data = await get_market_overview(db)
    return MarketOverviewResponse(**data)


@router.get("/segments", response_model=list[SegmentResponse])
async def segments_endpoint(
    axis: str | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    segments = await get_segments(db, axis)
    return [SegmentResponse(**s) for s in segments]


@router.get("/market-size", response_model=MarketSizeSeriesResponse)
async def market_size_endpoint(
    segment_code: str | None = Query(None),
    geography_code: str | None = Query(None),
    year_from: int | None = Query(None),
    year_to: int | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    data = await get_market_size_series(db, segment_code, geography_code, year_from, year_to)
    return MarketSizeSeriesResponse(
        data=data,
        segment_code=segment_code,
        geography_code=geography_code,
    )


@router.get("/companies", response_model=list[CompanyResponse])
async def companies_endpoint(
    search: str | None = Query(None),
    country: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    data = await get_companies(db, search, country, limit)
    return [CompanyResponse(**c) for c in data]


@router.get("/market-share", response_model=MarketShareResponse)
async def market_share_endpoint(
    segment_code: str = Query("all"),
    year: int | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    data = await get_market_share(db, segment_code, year)
    return MarketShareResponse(**data)


@router.get("/competitive-events", response_model=list[CompetitiveEventResponse])
async def competitive_events_endpoint(
    event_type: str | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    data = await get_competitive_events(db, event_type, limit)
    return [CompetitiveEventResponse(**e) for e in data]


@router.get("/insights", response_model=list[InsightResponse])
async def insights_endpoint(
    category: str | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    data = await get_insights(db, category)
    return [InsightResponse(**i) for i in data]


@router.post("/framework", response_model=FrameworkResponse)
async def framework_endpoint(
    body: FrameworkRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    data = await generate_framework(db, body.framework_type, body.parameters)
    return FrameworkResponse(**data)


@router.post("/refresh")
async def refresh_market_research(user: dict = Depends(get_current_user)):
    """Trigger market research agent in background."""

    def _run():
        from app.agents.market_research_agent import MarketResearchAgent
        from app.database import get_sync_db

        db = get_sync_db()
        try:
            agent = MarketResearchAgent(db)
            count = agent.fetch_data()
            agent.update_status("active", records=count)
        except Exception:
            pass

    asyncio.get_event_loop().run_in_executor(None, _run)
    return {"status": "refresh_triggered"}
