from datetime import datetime

from pydantic import BaseModel


class NewsArticleResponse(BaseModel):
    id: str
    title: str
    summary: str | None
    source_url: str
    source_name: str | None
    category: str | None
    tags: list[str] | None
    published_at: datetime | None
    relevance_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsQuery(BaseModel):
    category: str | None = None
    search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = 1
    per_page: int = 20


class NewsPaginatedResponse(BaseModel):
    data: list[NewsArticleResponse]
    total: int
    page: int
    per_page: int
