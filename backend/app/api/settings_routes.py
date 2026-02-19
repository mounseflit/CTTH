import asyncio
import logging
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db, get_sync_db
from app.schemas.email import EmailRecipientCreate, EmailRecipientResponse
from app.schemas.settings import APIKeyStatus, DataSourceStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _run_agent(source_name: str):
    """Run the appropriate agent synchronously."""
    from app.agents.comtrade_agent import ComtradeAgent
    from app.agents.eurostat_agent import EurostatAgent
    from app.agents.federal_register_agent import FederalRegisterAgent
    from app.agents.general_watcher import GeneralWatcher
    from app.agents.otexa_agent import OtexaAgent

    agent_map = {
        "eurostat_comext": EurostatAgent,
        "un_comtrade": ComtradeAgent,
        "federal_register": FederalRegisterAgent,
        "openai_search": GeneralWatcher,
        "otexa_tradegov": OtexaAgent,
    }
    cls = agent_map.get(source_name)
    if cls is None:
        return
    db = get_sync_db()
    agent = cls(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception(f"Agent {source_name} fetch failed")


@router.get("/data-sources", response_model=list[DataSourceStatusResponse])
async def get_data_sources(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    cursor = db.data_source_status.find({}).sort("source_name", 1)
    sources = await cursor.to_list(50)

    return [
        DataSourceStatusResponse(
            source_name=s.get("source_name", ""),
            status=s.get("status", "unknown"),
            last_successful_fetch=s.get("last_successful_fetch"),
            last_error_message=s.get("last_error_message"),
            records_fetched_today=s.get("records_fetched_today", 0),
            api_calls_today=s.get("api_calls_today", 0),
        )
        for s in sources
    ]


@router.post("/data-sources/{source_name}/refresh")
async def refresh_data_source(
    source_name: str,
    user: dict = Depends(get_current_user),
):
    valid = {"eurostat_comext", "un_comtrade", "federal_register", "openai_search", "otexa_tradegov"}
    if source_name not in valid:
        raise HTTPException(
            status_code=404, detail=f"Source inconnue: {source_name}"
        )

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _run_agent, source_name)
    return {"status": "refresh_triggered", "source": source_name}


@router.get("/api-keys", response_model=list[APIKeyStatus])
async def get_api_keys(user: dict = Depends(get_current_user)):
    def mask_key(key: str | None) -> str | None:
        if not key:
            return None
        if len(key) > 8:
            return key[:4] + "..." + key[-4:]
        return "****"

    return [
        APIKeyStatus(
            name="OpenAI API Key",
            configured=bool(settings.OPENAI_API_KEY),
            masked_value=mask_key(settings.OPENAI_API_KEY),
        ),
        APIKeyStatus(
            name="Comtrade Primary Key",
            configured=bool(settings.COMTRADE_PRIMARY_KEY),
            masked_value=mask_key(settings.COMTRADE_PRIMARY_KEY),
        ),
        APIKeyStatus(
            name="Gemini API Key",
            configured=bool(settings.GEMINI_API_KEY),
            masked_value=mask_key(settings.GEMINI_API_KEY),
        ),
    ]


# ── Email Recipients CRUD ──────────────────────────────────────────


@router.get("/email-recipients", response_model=list[EmailRecipientResponse])
async def get_email_recipients(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List saved email recipients for current user."""
    cursor = db.email_recipients.find({"user_id": user["_id"]}).sort("created_at", -1)
    docs = await cursor.to_list(100)
    return [
        EmailRecipientResponse(
            id=str(d["_id"]),
            email=d.get("email", ""),
            name=d.get("name", ""),
            created_at=d.get("created_at", datetime.now(timezone.utc)),
        )
        for d in docs
    ]


@router.post("/email-recipients", response_model=EmailRecipientResponse)
async def add_email_recipient(
    data: EmailRecipientCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Add a new email recipient."""
    email = data.email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=422, detail="Adresse email invalide")

    # Check for duplicate
    existing = await db.email_recipients.find_one({"user_id": user["_id"], "email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Ce destinataire existe deja")

    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": user["_id"],
        "email": email,
        "name": data.name.strip(),
        "created_at": datetime.now(timezone.utc),
    }
    await db.email_recipients.insert_one(doc)

    return EmailRecipientResponse(
        id=doc["_id"],
        email=doc["email"],
        name=doc["name"],
        created_at=doc["created_at"],
    )


@router.delete("/email-recipients/{recipient_id}")
async def delete_email_recipient(
    recipient_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Delete a saved email recipient."""
    result = await db.email_recipients.delete_one(
        {"_id": recipient_id, "user_id": user["_id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Destinataire non trouve")
    return {"status": "deleted", "id": recipient_id}
