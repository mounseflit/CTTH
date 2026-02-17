import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.database import get_db
from app.models.report import new_report_doc
from app.schemas.report import (
    ReportCreate,
    ReportListItem,
    ReportResponse,
    ReportStatusResponse,
)

router = APIRouter()


def _run_report_generation(report_id: str):
    """Run report generation synchronously (called from background task)."""
    from app.database import get_sync_db
    from app.services.report_service import ReportGenerationService

    db = get_sync_db()
    report = db.reports.find_one({"_id": report_id})
    if not report:
        return

    db.reports.update_one(
        {"_id": report_id},
        {"$set": {"status": "generating", "generation_started_at": datetime.now(timezone.utc)}},
    )

    try:
        service = ReportGenerationService(db)
        result = service.generate(report)
        db.reports.update_one(
            {"_id": report_id},
            {
                "$set": {
                    "status": "completed",
                    "content_markdown": result["content_markdown"],
                    "content_html": result["content_html"],
                    "pdf_path": result.get("pdf_path"),
                    "generation_completed_at": datetime.now(timezone.utc),
                }
            },
        )
    except Exception:
        db.reports.update_one({"_id": report_id}, {"$set": {"status": "failed"}})


@router.get("/", response_model=list[ReportListItem])
async def list_reports(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    cursor = (
        db.reports.find({"generated_by": user["_id"]})
        .sort("created_at", -1)
    )
    reports = await cursor.to_list(200)

    return [
        ReportListItem(
            id=str(r["_id"]),
            title=r.get("title", ""),
            report_type=r.get("report_type", ""),
            status=r.get("status", "pending"),
            created_at=r.get("created_at", datetime.now(timezone.utc)),
        )
        for r in reports
    ]


@router.post("/", response_model=ReportStatusResponse)
async def create_report(
    data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    doc = new_report_doc(
        title=data.title,
        report_type=data.report_type,
        generated_by=user["_id"],
        parameters=data.parameters,
    )
    await db.reports.insert_one(doc)

    # Dispatch report generation as a background task
    background_tasks.add_task(_run_report_generation, doc["_id"])

    return ReportStatusResponse(id=doc["_id"], status="pending")


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    report = await db.reports.find_one({"_id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Rapport non trouve")

    return ReportResponse(
        id=str(report["_id"]),
        title=report.get("title", ""),
        report_type=report.get("report_type", ""),
        status=report.get("status", "pending"),
        parameters=report.get("parameters"),
        content_markdown=report.get("content_markdown"),
        created_at=report.get("created_at", datetime.now(timezone.utc)),
        generation_started_at=report.get("generation_started_at"),
        generation_completed_at=report.get("generation_completed_at"),
    )


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
async def get_report_status(
    report_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    report = await db.reports.find_one({"_id": report_id}, {"_id": 1, "status": 1})
    if not report:
        raise HTTPException(status_code=404, detail="Rapport non trouve")

    return ReportStatusResponse(id=str(report["_id"]), status=report.get("status", "pending"))


@router.get("/{report_id}/pdf")
async def download_report_pdf(
    report_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    report = await db.reports.find_one({"_id": report_id}, {"pdf_path": 1})
    if not report or not report.get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF non disponible")

    return FileResponse(
        path=report["pdf_path"],
        media_type="application/pdf",
        filename=f"CTTH_Rapport_{report_id[:8]}.pdf",
    )
