"""Report document helpers for MongoDB."""
import uuid
from datetime import datetime, timezone


def new_report_doc(
    title: str,
    report_type: str,
    generated_by: str,
    parameters: dict | None = None,
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "title": title,
        "report_type": report_type,
        "status": "pending",
        "parameters": parameters,
        "content_markdown": None,
        "content_html": None,
        "pdf_path": None,
        "generated_by": generated_by,
        "generation_started_at": None,
        "generation_completed_at": None,
        "created_at": datetime.now(timezone.utc),
    }
