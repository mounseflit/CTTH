"""Report generation task — callable as a plain function (no Celery needed)."""

import logging
from datetime import datetime, timezone

from app.database import get_sync_db
from app.services.report_service import ReportGenerationService

logger = logging.getLogger(__name__)


def generate_report_task(report_id: str) -> dict:
    """Synchronous report generation."""
    db = get_sync_db()
    report = db.reports.find_one({"_id": report_id})
    if not report:
        logger.error(f"Report not found: {report_id}")
        return {"status": "error", "message": "Report not found"}

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
        return {"status": "completed", "report_id": report_id}
    except Exception:
        db.reports.update_one({"_id": report_id}, {"$set": {"status": "failed"}})
        logger.exception(f"Report generation failed: {report_id}")
        return {"status": "failed", "report_id": report_id}
