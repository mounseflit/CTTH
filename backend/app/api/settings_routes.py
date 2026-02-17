import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db, get_sync_db
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
