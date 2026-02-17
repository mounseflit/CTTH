from datetime import datetime

from pydantic import BaseModel


class KPICard(BaseModel):
    label: str
    value: str
    change_pct: float | None = None
    period: str = ""
    icon: str = ""


class TrendDataPoint(BaseModel):
    period: str
    exports: float
    imports: float


class RecentNewsItem(BaseModel):
    id: str
    title: str
    category: str | None
    source_name: str | None
    published_at: datetime | None


class DashboardResponse(BaseModel):
    kpi_cards: list[KPICard]
    trend_data: list[TrendDataPoint]
    recent_news: list[RecentNewsItem]
    top_partners: list[dict]
    hs_breakdown: list[dict]
