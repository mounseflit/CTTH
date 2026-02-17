from datetime import datetime

from pydantic import BaseModel


class ReportCreate(BaseModel):
    title: str
    report_type: str  # "weekly_summary", "market_analysis", "regulatory_alert", "custom"
    parameters: dict | None = None  # date_range, hs_codes, partners, etc.


class ReportResponse(BaseModel):
    id: str
    title: str
    report_type: str
    status: str
    parameters: dict | None
    content_markdown: str | None
    created_at: datetime
    generation_started_at: datetime | None
    generation_completed_at: datetime | None

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id: str
    title: str
    report_type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportStatusResponse(BaseModel):
    id: str
    status: str
