from datetime import date

from pydantic import BaseModel


class TradeDataQuery(BaseModel):
    hs_codes: list[str] | None = None
    partners: list[str] | None = None
    flow: str | None = None  # "import", "export", or None for both
    source: str | None = None  # "eurostat", "comtrade", or None for all
    date_from: date | None = None
    date_to: date | None = None
    frequency: str | None = None  # "A" or "M"
    page: int = 1
    per_page: int = 50


class TradeDataResponse(BaseModel):
    id: int
    period_date: str
    source: str
    reporter_code: str
    reporter_name: str | None
    partner_code: str
    partner_name: str | None
    hs_code: str
    hs_description: str | None
    flow: str
    value_usd: float | None
    value_eur: float | None
    weight_kg: float | None
    quantity: float | None
    frequency: str

    model_config = {"from_attributes": True}


class TradeAggregation(BaseModel):
    label: str
    value: float
    count: int | None = None
    change_pct: float | None = None


class TradePaginatedResponse(BaseModel):
    data: list[TradeDataResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
