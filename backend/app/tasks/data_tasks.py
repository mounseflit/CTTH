"""Data-fetching tasks — callable as plain functions (no Celery needed)."""

import logging

from app.agents.comtrade_agent import ComtradeAgent
from app.agents.eurostat_agent import EurostatAgent
from app.agents.federal_register_agent import FederalRegisterAgent
from app.agents.general_watcher import GeneralWatcher
from app.database import get_sync_db

logger = logging.getLogger(__name__)


def fetch_eurostat_data():
    """Fetch trade data from Eurostat Comext."""
    db = get_sync_db()
    agent = EurostatAgent(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        return {"source": "eurostat", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("Eurostat fetch failed")
        return {"source": "eurostat", "status": "error", "message": str(exc)}


def fetch_comtrade_data():
    """Fetch trade data from UN Comtrade."""
    db = get_sync_db()
    agent = ComtradeAgent(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        return {"source": "comtrade", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("Comtrade fetch failed")
        return {"source": "comtrade", "status": "error", "message": str(exc)}


def fetch_federal_register():
    """Fetch regulatory news from Federal Register."""
    db = get_sync_db()
    agent = FederalRegisterAgent(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        return {"source": "federal_register", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("Federal Register fetch failed")
        return {"source": "federal_register", "status": "error", "message": str(exc)}


def fetch_general_news():
    """Fetch general news using OpenAI web search."""
    db = get_sync_db()
    agent = GeneralWatcher(db)
    try:
        count = agent.fetch_data()
        agent.update_status("active", records=count)
        return {"source": "openai_search", "records": count, "status": "success"}
    except Exception as exc:
        agent.update_status("error", error_msg=str(exc))
        logger.exception("General watcher fetch failed")
        return {"source": "openai_search", "status": "error", "message": str(exc)}


def reset_daily_counters():
    """Reset daily API call and record counters."""
    db = get_sync_db()
    db.data_source_status.update_many({}, {"$set": {"records_fetched_today": 0, "api_calls_today": 0}})
    return {"status": "counters_reset"}
