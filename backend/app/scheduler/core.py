"""APScheduler setup and lifecycle management."""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = logging.getLogger("scheduler.core")

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler | None:
    """Return the scheduler instance (None if not initialized)."""
    return _scheduler


def init_scheduler() -> AsyncIOScheduler | None:
    """Create and configure the scheduler. Does NOT start it."""
    global _scheduler

    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler is DISABLED via SCHEDULER_ENABLED=false")
        return None

    _scheduler = AsyncIOScheduler(
        job_defaults={
            "coalesce": True,           # If multiple runs missed, only run once
            "max_instances": 1,         # Never run the same job concurrently
            "misfire_grace_time": 3600, # Allow up to 1h late execution
        },
        timezone="UTC",
    )

    # Register the daily pipeline as a cron job
    from app.scheduler.pipeline import run_daily_pipeline

    _scheduler.add_job(
        run_daily_pipeline,
        trigger=CronTrigger(
            hour=settings.SCHEDULER_DAILY_HOUR,
            minute=settings.SCHEDULER_DAILY_MINUTE,
            timezone="UTC",
        ),
        id="daily_pipeline",
        name="Daily Data Pipeline",
        replace_existing=True,
    )

    logger.info(
        f"Scheduler configured: daily pipeline at "
        f"{settings.SCHEDULER_DAILY_HOUR:02d}:{settings.SCHEDULER_DAILY_MINUTE:02d} UTC"
    )

    return _scheduler


def start_scheduler():
    """Start the scheduler if it exists and is not already running."""
    if _scheduler and not _scheduler.running:
        _scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler():
    """Shutdown the scheduler gracefully."""
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
