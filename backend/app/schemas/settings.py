from datetime import datetime

from pydantic import BaseModel


class DataSourceStatusResponse(BaseModel):
    source_name: str
    status: str
    last_successful_fetch: datetime | None
    last_error_message: str | None
    records_fetched_today: int
    api_calls_today: int

    model_config = {"from_attributes": True}


class APIKeyStatus(BaseModel):
    name: str
    configured: bool
    masked_value: str | None = None
