from datetime import datetime

from pydantic import BaseModel, EmailStr


class EmailRecipientCreate(BaseModel):
    email: str
    name: str = ""


class EmailRecipientResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SendEmailRequest(BaseModel):
    recipient_ids: list[str] = []
    extra_emails: list[str] = []
