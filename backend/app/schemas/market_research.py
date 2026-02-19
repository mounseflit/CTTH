"""Pydantic response models for market research endpoints."""
from datetime import datetime

from pydantic import BaseModel


class MarketOverviewResponse(BaseModel):
    total_market_size_usd: float
    market_size_formatted: str
    growth_pct: float | None = None
    trade_balance_usd: float
    export_total_usd: float
    import_total_usd: float
    segment_count: int
    company_count: int
    insight_count: int
    latest_year: int


class SegmentResponse(BaseModel):
    id: str
    axis: str
    code: str
    label_fr: str
    label_en: str = ""
    parent_code: str | None = None
    description_fr: str = ""
    market_value: float | None = None


class MarketSizePoint(BaseModel):
    year: int
    value_usd: float
    flow: str = "total"
    segment_code: str = ""
    geography_code: str = ""


class MarketSizeSeriesResponse(BaseModel):
    data: list[MarketSizePoint]
    segment_code: str | None = None
    geography_code: str | None = None


class SWOTResponse(BaseModel):
    strengths: list[str] = []
    weaknesses: list[str] = []
    opportunities: list[str] = []
    threats: list[str] = []


class CompanyResponse(BaseModel):
    id: str
    name: str
    country: str = "MA"
    hq_city: str = ""
    description_fr: str = ""
    swot: SWOTResponse = SWOTResponse()
    financials: dict = {}
    executives: list[dict] = []
    website: str | None = ""
    sector: str = "textile"
    market_share_pct: float | None = None

    model_config = {"from_attributes": True}


class MarketShareEntry(BaseModel):
    company_name: str
    share_pct: float
    value_usd: float = 0


class MarketShareResponse(BaseModel):
    year: int
    segment_code: str
    entries: list[MarketShareEntry]


class CompetitiveEventResponse(BaseModel):
    id: str
    event_type: str
    company_name: str
    title: str
    description_fr: str = ""
    event_date: datetime | None = None
    source_url: str = ""
    source_name: str = ""

    model_config = {"from_attributes": True}


class InsightResponse(BaseModel):
    id: str
    category: str
    title: str
    narrative_fr: str
    droc_type: str | None = None
    tags: list[str] = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class FrameworkRequest(BaseModel):
    framework_type: str  # "porter", "pestel", "tam_sam_som"
    parameters: dict | None = None


class FrameworkResponse(BaseModel):
    id: str
    framework_type: str
    content: dict
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
