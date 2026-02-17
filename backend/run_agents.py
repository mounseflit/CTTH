"""
Run all data-collection agents sequentially and print results.
Usage:  python run_agents.py
"""
import logging
import sys
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-30s %(levelname)-7s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("run_agents")

from app.database import get_sync_db

db = get_sync_db()
logger.info("Connected to MongoDB — database: %s", db.name)


# ── 1. Eurostat ──────────────────────────────────────────
logger.info("=" * 60)
logger.info("RUNNING: EurostatAgent")
try:
    from app.agents.eurostat_agent import EurostatAgent
    n = EurostatAgent(db).fetch_data()
    logger.info("EurostatAgent finished — %d records", n)
except Exception:
    logger.error("EurostatAgent FAILED:\n%s", traceback.format_exc())

# ── 2. Comtrade ──────────────────────────────────────────
logger.info("=" * 60)
logger.info("RUNNING: ComtradeAgent")
try:
    from app.agents.comtrade_agent import ComtradeAgent
    n = ComtradeAgent(db).fetch_data()
    logger.info("ComtradeAgent finished — %d records", n)
except Exception:
    logger.error("ComtradeAgent FAILED:\n%s", traceback.format_exc())

# ── 3. Federal Register ─────────────────────────────────
logger.info("=" * 60)
logger.info("RUNNING: FederalRegisterAgent")
try:
    from app.agents.federal_register_agent import FederalRegisterAgent
    n = FederalRegisterAgent(db).fetch_data()
    logger.info("FederalRegisterAgent finished — %d records", n)
except Exception:
    logger.error("FederalRegisterAgent FAILED:\n%s", traceback.format_exc())

# ── 4. General Watcher (OpenAI + Gemini) ─────────────────
logger.info("=" * 60)
logger.info("RUNNING: GeneralWatcher")
try:
    from app.agents.general_watcher import GeneralWatcher
    n = GeneralWatcher(db).fetch_data()
    logger.info("GeneralWatcher finished — %d records", n)
except Exception:
    logger.error("GeneralWatcher FAILED:\n%s", traceback.format_exc())

# ── 5. OTEXA Agent (OpenAI web search) ──────────────────
logger.info("=" * 60)
logger.info("RUNNING: OtexaAgent")
try:
    from app.agents.otexa_agent import OtexaAgent
    n = OtexaAgent(db).fetch_data()
    logger.info("OtexaAgent finished — %d records", n)
except Exception:
    logger.error("OtexaAgent FAILED:\n%s", traceback.format_exc())


# ── Summary ──────────────────────────────────────────────
logger.info("=" * 60)
logger.info("DATA COLLECTION COMPLETE")
logger.info("  trade_data count:    %d", db.trade_data.count_documents({}))
logger.info("  news_articles count: %d", db.news_articles.count_documents({}))
logger.info("=" * 60)
