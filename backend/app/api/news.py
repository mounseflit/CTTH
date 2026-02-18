from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.database import get_db
from app.schemas.news import NewsArticleResponse, NewsPaginatedResponse
from app.services.news_service import get_news

router = APIRouter()


@router.get("", response_model=NewsPaginatedResponse)
async def get_news_endpoint(
    category: str | None = Query(None),
    search: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    articles, total = await get_news(
        db, category, search, date_from, date_to, page, per_page
    )

    return NewsPaginatedResponse(
        data=[
            NewsArticleResponse(
                id=str(a.get("_id", "")),
                title=a.get("title", ""),
                summary=a.get("summary"),
                source_url=a.get("source_url", ""),
                source_name=a.get("source_name"),
                category=a.get("category"),
                tags=a.get("tags") if isinstance(a.get("tags"), list) else [],
                published_at=a.get("published_at"),
                relevance_score=a.get("relevance_score"),
                created_at=a.get("created_at", datetime.now()),
            )
            for a in articles
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{article_id}", response_model=NewsArticleResponse)
async def get_news_article(
    article_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    article = await db.news_articles.find_one({"_id": article_id})

    if not article:
        raise HTTPException(status_code=404, detail="Article non trouve")

    return NewsArticleResponse(
        id=str(article["_id"]),
        title=article.get("title", ""),
        summary=article.get("summary"),
        source_url=article.get("source_url", ""),
        source_name=article.get("source_name"),
        category=article.get("category"),
        tags=article.get("tags") if isinstance(article.get("tags"), list) else [],
        published_at=article.get("published_at"),
        relevance_score=article.get("relevance_score"),
        created_at=article.get("created_at", datetime.now()),
    )


@router.post("/refresh")
async def refresh_news(user: dict = Depends(get_current_user)):
    """Manually trigger news fetch in background."""
    import asyncio

    from app.agents.federal_register_agent import FederalRegisterAgent
    from app.agents.general_watcher import GeneralWatcher
    from app.agents.otexa_agent import OtexaAgent

    def _run():
        from app.database import get_sync_db
        db = get_sync_db()
        try:
            FederalRegisterAgent(db).fetch_data()
        except Exception:
            pass
        try:
            GeneralWatcher(db).fetch_data()
        except Exception:
            pass
        try:
            OtexaAgent(db).fetch_data()
        except Exception:
            pass

    asyncio.get_event_loop().run_in_executor(None, _run)
    return {"status": "refresh_triggered"}
