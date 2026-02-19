"""Daily pipeline orchestrator.

Called by APScheduler once per day. Runs all phases in sequence,
logging results and updating a pipeline run status in MongoDB.
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger("scheduler.pipeline")

# Reusable thread pool for sync agent jobs
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sched")


async def run_daily_pipeline():
    """Main daily pipeline entry point. Called by APScheduler as an async job."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logger.info(f"[pipeline:{run_id}] Starting daily pipeline")

    start_time = datetime.now(timezone.utc)
    phase_results: dict = {}
    loop = asyncio.get_running_loop()

    # Import jobs lazily
    from app.scheduler.jobs import (
        job_derive_market_data,
        job_fetch_comtrade,
        job_fetch_eurostat,
        job_fetch_federal_register,
        job_fetch_market_research,
        job_fetch_news,
        job_fetch_otexa,
        job_generate_frameworks,
        job_reset_daily_counters,
    )

    # ── Phase 1: Trade data agents (parallel in threads) ────
    logger.info(f"[pipeline:{run_id}] Phase 1: Trade data agents")
    futures = [
        loop.run_in_executor(_executor, job_fetch_eurostat),
        loop.run_in_executor(_executor, job_fetch_comtrade),
        loop.run_in_executor(_executor, job_fetch_federal_register),
        loop.run_in_executor(_executor, job_fetch_otexa),
    ]
    results = await asyncio.gather(*futures, return_exceptions=True)
    phase_results["trade_agents"] = [
        r if not isinstance(r, Exception) else {"status": "error", "message": str(r)}
        for r in results
    ]

    # ── Phase 2: News agent ─────────────────────────────────
    logger.info(f"[pipeline:{run_id}] Phase 2: News agent")
    try:
        result = await loop.run_in_executor(_executor, job_fetch_news)
        phase_results["news_agent"] = result
    except Exception as exc:
        phase_results["news_agent"] = {"status": "error", "message": str(exc)}

    # ── Phase 3: Market research agent ──────────────────────
    logger.info(f"[pipeline:{run_id}] Phase 3: Market research agent")
    try:
        result = await loop.run_in_executor(_executor, job_fetch_market_research)
        phase_results["market_research"] = result
    except Exception as exc:
        phase_results["market_research"] = {"status": "error", "message": str(exc)}

    # ── Phase 4: Derive market data ─────────────────────────
    logger.info(f"[pipeline:{run_id}] Phase 4: Derive market data")
    try:
        result = await loop.run_in_executor(_executor, job_derive_market_data)
        phase_results["derive_data"] = result
    except Exception as exc:
        phase_results["derive_data"] = {"status": "error", "message": str(exc)}

    # ── Phase 5: Framework generation (async) ───────────────
    logger.info(f"[pipeline:{run_id}] Phase 5: Framework generation")
    try:
        result = await job_generate_frameworks()
        phase_results["frameworks"] = result
    except Exception as exc:
        phase_results["frameworks"] = {"status": "error", "message": str(exc)}

    # ── Phase 6: Reset daily counters ───────────────────────
    logger.info(f"[pipeline:{run_id}] Phase 6: Reset counters")
    try:
        result = await loop.run_in_executor(_executor, job_reset_daily_counters)
        phase_results["reset_counters"] = result
    except Exception as exc:
        phase_results["reset_counters"] = {"status": "error", "message": str(exc)}

    # ── Store pipeline run result in MongoDB ────────────────
    end_time = datetime.now(timezone.utc)
    duration_seconds = (end_time - start_time).total_seconds()

    from app.database import get_async_db

    db = get_async_db()
    await db.scheduler_runs.insert_one({
        "_id": run_id,
        "started_at": start_time,
        "completed_at": end_time,
        "duration_seconds": duration_seconds,
        "phase_results": phase_results,
        "status": "completed",
    })

    logger.info(f"[pipeline:{run_id}] Daily pipeline completed in {duration_seconds:.1f}s")
