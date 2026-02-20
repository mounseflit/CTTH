from datetime import date

from pydantic import BaseModel, field_validator


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


class DeepAnalysisRequest(BaseModel):
    hs_code: str  # e.g. "61" (chapter), "610210" (full code)
    year: int

    @field_validator("hs_code")
    @classmethod
    def hs_code_must_be_numeric(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("hs_code must contain only digits")
        return v

    @field_validator("year")
    @classmethod
    def year_in_range(cls, v: int) -> int:
        if v < 2000 or v > 2030:
            raise ValueError("year must be between 2000 and 2030")
        return v


class DeepAnalysisShareRequest(DeepAnalysisRequest):
    """Share deep analysis by email — extends DeepAnalysisRequest with recipient info."""
    recipient_ids: list[str] = []
    extra_emails: list[str] = []
