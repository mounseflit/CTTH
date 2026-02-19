"""Scheduler status and control API routes."""
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class SchedulerStatusResponse(BaseModel):
    enabled: bool
    running: bool
    jobs: list[dict]


class PipelineRunResponse(BaseModel):
    id: str
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None
    status: str
    phase_results: dict | None = None


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(user: dict = Depends(get_current_user)):
    """Get current scheduler status and registered jobs."""
    from app.config import settings
    from app.scheduler.core import get_scheduler

    scheduler = get_scheduler()

    if scheduler is None:
        return SchedulerStatusResponse(
            enabled=settings.SCHEDULER_ENABLED, running=False, jobs=[]
        )

    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger),
        })

    return SchedulerStatusResponse(
        enabled=settings.SCHEDULER_ENABLED,
        running=scheduler.running,
        jobs=jobs,
    )


@router.post("/trigger")
async def trigger_daily_pipeline(user: dict = Depends(get_current_user)):
    """Manually trigger the daily pipeline immediately."""
    from app.scheduler.pipeline import run_daily_pipeline

    asyncio.get_event_loop().create_task(run_daily_pipeline())
    return {"status": "pipeline_triggered", "message": "Pipeline quotidien lance en arriere-plan"}


@router.get("/runs", response_model=list[PipelineRunResponse])
async def get_pipeline_runs(
    limit: int = 10,
    user: dict = Depends(get_current_user),
):
    """Get recent pipeline run history."""
    from app.database import get_async_db

    db = get_async_db()
    cursor = db.scheduler_runs.find({}).sort("started_at", -1).limit(limit)
    runs = await cursor.to_list(limit)

    return [
        PipelineRunResponse(
            id=str(r["_id"]),
            started_at=r["started_at"],
            completed_at=r.get("completed_at"),
            duration_seconds=r.get("duration_seconds"),
            status=r.get("status", "unknown"),
            phase_results=r.get("phase_results"),
        )
        for r in runs
    ]
