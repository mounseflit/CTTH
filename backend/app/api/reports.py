import logging
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.report import new_report_doc
from app.schemas.email import SendEmailRequest
from app.schemas.report import (
    ReportCreate,
    ReportListItem,
    ReportResponse,
    ReportStatusResponse,
)

logger = logging.getLogger(__name__)

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


@router.get("", response_model=list[ReportListItem])
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


@router.post("", response_model=ReportStatusResponse)
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


def _build_email_html(title: str, markdown_content: str, report_type: str, created_at: str) -> str:
    """Convert report markdown to professional HTML email."""
    import re as _re

    html = markdown_content

    # Tables: convert markdown tables to HTML tables
    def _convert_table(match: _re.Match) -> str:
        lines = match.group(0).strip().split("\n")
        rows = [l for l in lines if not _re.match(r"^\s*\|[-:\s|]+\|\s*$", l)]
        table_html = '<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:13px;">'
        for i, row in enumerate(rows):
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            style_th = 'style="background:#3fa69c;color:#fff;padding:10px 12px;text-align:left;font-size:12px;"'
            style_td = 'style="padding:10px 12px;border-bottom:1px solid #e0e5e5;color:#555e5e;"'
            style = style_th if i == 0 else style_td
            row_style = ' style="background:#f8fafa;"' if i % 2 == 0 and i > 0 else ""
            table_html += f"<tr{row_style}>" + "".join(f"<{tag} {style}>{c}</{tag}>" for c in cells) + "</tr>"
        table_html += "</table>"
        return table_html

    html = _re.sub(r"(\|.+\|[\n\r]+)+", _convert_table, html)

    # Blockquotes
    html = _re.sub(
        r"^> (.+)$",
        r'<div style="border-left:4px solid #3fa69c;padding:12px 16px;background:#f0faf9;margin:16px 0;border-radius:0 8px 8px 0;"><p style="margin:0;color:#353A3A;font-size:13px;">\1</p></div>',
        html, flags=_re.MULTILINE,
    )

    # Headings
    html = _re.sub(r"^### (.+)$", r'<h3 style="color:#353A3A;font-size:15px;margin:20px 0 8px;font-weight:700;">\1</h3>', html, flags=_re.MULTILINE)
    html = _re.sub(r"^## (.+)$", r'<h2 style="color:#353A3A;font-size:17px;margin:24px 0 10px;border-bottom:2px solid #C1DEDB;padding-bottom:8px;font-weight:700;">\1</h2>', html, flags=_re.MULTILINE)
    html = _re.sub(r"^# (.+)$", r'<h1 style="color:#353A3A;font-size:20px;margin:28px 0 12px;font-weight:800;">\1</h1>', html, flags=_re.MULTILINE)

    # Bold & italic
    html = _re.sub(r"\*\*(.+?)\*\*", r"<strong style='color:#353A3A;'>\1</strong>", html)
    html = _re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    # Horizontal rules
    html = _re.sub(r"^---+$", '<hr style="border:none;height:2px;background:linear-gradient(90deg,#3fa69c,#C1DEDB);margin:24px 0;">', html, flags=_re.MULTILINE)

    # Numbered lists
    html = _re.sub(r"^\d+\. (.+)$", r'<li style="margin:4px 0;color:#555e5e;">\1</li>', html, flags=_re.MULTILINE)

    # Bullet lists
    html = _re.sub(r"^- (.+)$", r'<li style="margin:4px 0;color:#555e5e;">\1</li>', html, flags=_re.MULTILINE)
    html = _re.sub(r"(<li[^>]*>.*</li>\n?)+", r'<ul style="padding-left:20px;margin:10px 0;">\g<0></ul>', html)

    # Paragraphs
    html = _re.sub(r"\n\n", '</p><p style="color:#555e5e;line-height:1.7;margin:10px 0;">', html)

    # Report type label
    TYPE_LABELS = {
        "weekly_summary": "Resume Hebdomadaire",
        "market_analysis": "Analyse de Marche",
        "market_research": "Etude de Marche",
        "regulatory_alert": "Alerte Reglementaire",
        "custom": "Rapport Personnalise",
    }
    type_label = TYPE_LABELS.get(report_type, "Rapport")
    date_str = ""
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%d/%m/%Y")
        except Exception:
            date_str = str(created_at)[:10]

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f0f3f3;font-family:'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f3f3;padding:40px 20px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(53,58,58,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,#3fa69c 0%,#58B9AF 50%,#7ddbd3 100%);padding:32px 40px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <img src="https://www.ctth.ma/wp-content/uploads/2021/05/logo-CTTH-FINAL-2.jpg" alt="CTTH" width="48" height="48" style="border-radius:12px;display:block;" />
                </td>
                <td style="padding-left:16px;">
                  <p style="margin:0;font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;">CTTH</p>
                  <p style="margin:2px 0 0;font-size:11px;color:rgba(255,255,255,0.8);letter-spacing:1px;text-transform:uppercase;">Centre Technique du Textile et de l'Habillement</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background:#353A3A;padding:16px 40px;">
            <p style="margin:0;font-size:18px;font-weight:700;color:#ffffff;">{title}</p>
            <p style="margin:6px 0 0;font-size:12px;color:#C1DEDB;">
              {type_label} &middot; {date_str} &middot; Genere par IA
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 40px;">
            <p style="color:#555e5e;line-height:1.7;margin:0 0 10px;">
              {html}
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f8fafa;padding:24px 40px;border-top:1px solid #e0e5e5;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <p style="margin:0;font-size:11px;color:#8a9494;">
                    Ce rapport a ete genere automatiquement par la plateforme de veille CTTH.
                  </p>
                  <p style="margin:4px 0 0;font-size:11px;color:#8a9494;">
                    &copy; {datetime.now().year} CTTH &mdash; Centre Technique du Textile et de l'Habillement
                  </p>
                </td>
                <td align="right">
                  <a href="https://www.ctth.ma" style="display:inline-block;padding:8px 16px;background:#58B9AF;color:#ffffff;text-decoration:none;border-radius:8px;font-size:12px;font-weight:600;">
                    Visiter ctth.ma
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


@router.post("/{report_id}/send-email")
async def send_report_email(
    report_id: str,
    body: SendEmailRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Send report by email to selected recipients."""
    # Get the report
    report = await db.reports.find_one({"_id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Rapport non trouve")
    if report.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Le rapport n'est pas encore termine")

    # Collect email addresses
    emails: list[str] = list(body.extra_emails)

    if body.recipient_ids:
        cursor = db.email_recipients.find(
            {"_id": {"$in": body.recipient_ids}, "user_id": user["_id"]}
        )
        saved = await cursor.to_list(100)
        for s in saved:
            if s.get("email") and s["email"] not in emails:
                emails.append(s["email"])

    if not emails:
        raise HTTPException(status_code=400, detail="Aucun destinataire specifie")

    # Build email HTML
    title = report.get("title", "Rapport CTTH")
    content = report.get("content_markdown", "Rapport en cours de preparation.")
    report_type = report.get("report_type", "custom")
    created_at = str(report.get("created_at", ""))

    html_email = _build_email_html(title, content, report_type, created_at)
    subject = f"CTTH — {title}"

    # Send to each recipient (primary URL, fallback on error/non-200)
    results = []
    payload_base = {
        "cc": "",
        "bcc": "",
        "isHtml": True,
        "attachments": [],
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        for email_addr in emails:
            payload = {**payload_base, "to": email_addr, "subject": subject, "message": html_email}
            sent = False
            last_error = ""
            for url in [settings.MAIL_API_URL, settings.MAIL_API_FALLBACK_URL]:
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        results.append({"email": email_addr, "status": "sent", "endpoint": url})
                        sent = True
                        break
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                        logger.warning(f"Mail API {url} returned {resp.status_code} for {email_addr}, trying fallback")
                except Exception as exc:
                    last_error = str(exc)
                    logger.warning(f"Mail API {url} exception for {email_addr}: {exc}, trying fallback")
            if not sent:
                results.append({"email": email_addr, "status": "error", "detail": last_error})

    sent_count = sum(1 for r in results if r["status"] == "sent")
    return {
        "total": len(emails),
        "sent": sent_count,
        "failed": len(emails) - sent_count,
        "results": results,
    }
