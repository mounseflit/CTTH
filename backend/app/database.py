import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.database import Database

from app.config import settings

logger = logging.getLogger(__name__)

_db_name = "ctth"

# --- Async client (Motor) for FastAPI routes ---
_async_client: AsyncIOMotorClient | None = None
_async_db: AsyncIOMotorDatabase | None = None

# --- Sync client (PyMongo) for agents & scripts ---
_sync_client: MongoClient | None = None
_sync_db: Database | None = None


def get_async_client() -> AsyncIOMotorClient:
    global _async_client
    if _async_client is None:
        _async_client = AsyncIOMotorClient(settings.MONGODB_URL)
    return _async_client


def get_async_db() -> AsyncIOMotorDatabase:
    global _async_db
    if _async_db is None:
        _async_db = get_async_client()[_db_name]
    return _async_db


def get_sync_client() -> MongoClient:
    global _sync_client
    if _sync_client is None:
        _sync_client = MongoClient(settings.MONGODB_URL)
    return _sync_client


def get_sync_db() -> Database:
    global _sync_db
    if _sync_db is None:
        _sync_db = get_sync_client()[_db_name]
    return _sync_db


async def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency: returns the async Motor database handle."""
    return get_async_db()


async def create_indexes():
    """Create all required indexes on startup."""
    db = get_async_db()

    # Users
    await db.users.create_index("email", unique=True)

    # Trade data — compound unique for upsert
    await db.trade_data.create_index(
        [
            ("source", 1),
            ("reporter_code", 1),
            ("partner_code", 1),
            ("hs_code", 1),
            ("flow", 1),
            ("period_date", 1),
            ("frequency", 1),
        ],
        unique=True,
        name="uq_trade_data_composite",
    )
    await db.trade_data.create_index("hs_code")
    await db.trade_data.create_index([("source", 1), ("flow", 1)])
    await db.trade_data.create_index("period_date")
    # Compound indexes for the most frequent query patterns
    await db.trade_data.create_index(
        [("flow", 1), ("period_date", 1)],
        name="idx_trade_flow_period",
    )
    await db.trade_data.create_index("partner_code", name="idx_trade_partner_code")

    # News articles
    await db.news_articles.create_index("source_url", unique=True)
    await db.news_articles.create_index("category")
    await db.news_articles.create_index("published_at")
    await db.news_articles.create_index("created_at")

    # Reports
    await db.reports.create_index("generated_by")
    await db.reports.create_index("status")

    # Data source status
    await db.data_source_status.create_index("source_name", unique=True)

    # Market research collections
    await db.market_segments.create_index(
        [("axis", 1), ("code", 1)], unique=True, name="uq_segment_axis_code"
    )
    await db.market_size_series.create_index(
        [("segment_code", 1), ("geography_code", 1), ("year", 1), ("flow", 1)],
        unique=True,
        name="uq_market_size_composite",
    )
    await db.companies.create_index("name", unique=True)
    await db.market_share_series.create_index(
        [("company_name", 1), ("segment_code", 1), ("year", 1)],
        unique=True,
        name="uq_market_share_composite",
    )
    await db.competitive_events.create_index([("event_date", -1)])
    await db.competitive_events.create_index("company_name")
    await db.insights.create_index("category")
    await db.insights.create_index([("created_at", -1)])
    await db.framework_results.create_index([("framework_type", 1), ("created_at", -1)])

    # Scheduler runs
    await db.scheduler_runs.create_index([("started_at", -1)])

    # Email recipients
    await db.email_recipients.create_index(
        [("user_id", 1), ("email", 1)], unique=True, name="uq_email_recipient_user"
    )

    logger.info("MongoDB indexes created/verified")


async def close_connections():
    """Close MongoDB connections on shutdown."""
    global _async_client, _sync_client, _async_db, _sync_db
    if _async_client:
        _async_client.close()
        _async_client = None
        _async_db = None
    if _sync_client:
        _sync_client.close()
        _sync_client = None
        _sync_db = None
