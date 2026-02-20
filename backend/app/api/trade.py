import logging
import os
import re as _re
from datetime import date, datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.schemas.trade import DeepAnalysisRequest, DeepAnalysisShareRequest, TradeDataResponse, TradePaginatedResponse
from app.services.trade_service import (
    get_aggregated_data,
    get_hs_breakdown,
    get_top_partners,
    get_trade_data,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/data", response_model=TradePaginatedResponse)
async def get_trade_data_endpoint(
    hs_codes: str | None = Query(None, description="Comma-separated HS codes"),
    partners: str | None = Query(None, description="Comma-separated partner codes"),
    flow: str | None = Query(None, description="import, export, or all"),
    source: str | None = Query(None, description="eurostat, comtrade, or all"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    frequency: str | None = Query(None, description="A or M"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    hs_list = hs_codes.split(",") if hs_codes else None
    partner_list = partners.split(",") if partners else None

    data, total = await get_trade_data(
        db,
        hs_codes=hs_list,
        partners=partner_list,
        flow=flow,
        source=source,
        date_from=date_from,
        date_to=date_to,
        frequency=frequency,
        page=page,
        per_page=per_page,
    )

    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    return TradePaginatedResponse(
        data=[
            TradeDataResponse(
                id=i + 1,  # Auto-increment style ID for frontend
                period_date=str(d.get("period_date", ""))[:10],
                source=d.get("source", ""),
                reporter_code=d.get("reporter_code", ""),
                reporter_name=d.get("reporter_name"),
                partner_code=d.get("partner_code", ""),
                partner_name=d.get("partner_name"),
                hs_code=d.get("hs_code", ""),
                hs_description=d.get("hs_description"),
                flow=d.get("flow", ""),
                value_usd=d.get("value_usd"),
                value_eur=d.get("value_eur"),
                weight_kg=d.get("weight_kg"),
                quantity=d.get("quantity"),
                frequency=d.get("frequency", "A"),
            )
            for i, d in enumerate(data)
        ],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/aggregated")
async def get_aggregated(
    group_by: str = Query("partner", description="partner, hs_code, period, flow"),
    flow: str | None = Query(None),
    source: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await get_aggregated_data(db, group_by, flow, source, date_from, date_to)


@router.get("/top-partners")
async def get_top_partners_endpoint(
    flow: str | None = Query(None),
    year: int | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await get_top_partners(db, flow, year, limit)


@router.get("/hs-breakdown")
async def get_hs_breakdown_endpoint(
    flow: str | None = Query(None),
    year: int | None = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return await get_hs_breakdown(db, flow, year)


@router.post("/deep-analysis")
async def deep_analysis_endpoint(
    body: DeepAnalysisRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Deep product analysis: trade data + frameworks + recommendations for a specific HS code and year."""
    from app.services.product_analysis_service import run_deep_analysis
    return await run_deep_analysis(db, body.hs_code, body.year)


# ── Deep analysis PDF + Email helpers ─────────────────────────────────────────

def _fmt_usd(val: float) -> str:
    abs_v = abs(val)
    sign = "-" if val < 0 else ""
    if abs_v >= 1e9:
        return f"{sign}${abs_v / 1e9:.1f}B"
    if abs_v >= 1e6:
        return f"{sign}${abs_v / 1e6:.1f}M"
    if abs_v >= 1e3:
        return f"{sign}${abs_v / 1e3:.0f}K"
    return f"{sign}${abs_v:.0f}"


def _render_val(val) -> str:
    """Render a framework value (could be string, list of dicts, etc.) to text."""
    if val is None:
        return "N/A"
    if isinstance(val, str):
        return val
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, list):
        parts = []
        for item in val:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("description") or item.get("factor") or ""
                parts.append(str(text) if text else str(item))
            else:
                parts.append(str(item))
        return "\n".join(f"• {p}" for p in parts)
    if isinstance(val, dict):
        text = val.get("text") or val.get("description") or val.get("summary") or val.get("factor")
        if text:
            return str(text)
        return "; ".join(f"{k}: {v}" for k, v in val.items())
    return str(val)


def _build_deep_analysis_markdown(data: dict) -> str:
    """Convert deep analysis result dict to professional Markdown for email/PDF."""
    md = []
    hs = data.get("hs_code", "")
    desc = data.get("hs_description", "Produit textile")
    year = data.get("year", "")
    export_usd = data.get("export_total_usd", 0)
    import_usd = data.get("import_total_usd", 0)
    balance = data.get("trade_balance_usd", 0)
    trend_pct = data.get("trend_pct", 0)
    trend_dir = data.get("trend_direction", "stable")

    md.append(f"# Analyse Produit — HS {hs} ({year})")
    md.append(f"\n**{desc}**\n")

    # KPI overview
    md.append("## Vue d'ensemble\n")
    md.append(f"| Indicateur | Valeur |")
    md.append(f"|---|---|")
    md.append(f"| Exports | {_fmt_usd(export_usd)} |")
    md.append(f"| Imports | {_fmt_usd(import_usd)} |")
    md.append(f"| Balance commerciale | {_fmt_usd(balance)} |")
    md.append(f"| Tendance export | {'+' if trend_pct > 0 else ''}{trend_pct}% ({trend_dir}) |")
    md.append("")

    # Trend probability
    fw = data.get("frameworks") or {}
    tp = fw.get("trend_probability")
    if tp:
        md.append(f"**Probabilite de tendance haussiere : {tp.get('upward_pct', 'N/A')}%**")
        if tp.get("justification"):
            md.append(f"\n> {tp['justification']}\n")

    # Trend data table
    trend_data = data.get("trade_trend", [])
    if trend_data:
        md.append("## Evolution annuelle\n")
        md.append("| Annee | Exports | Imports |")
        md.append("|---|---|---|")
        for t in trend_data:
            md.append(f"| {t.get('year', '')} | {_fmt_usd(t.get('export_usd', 0))} | {_fmt_usd(t.get('import_usd', 0))} |")
        md.append("")

    # Top partners
    for label, key in [("Destinations export", "export_partners"), ("Sources import", "import_partners")]:
        partners = data.get(key, [])
        if partners:
            md.append(f"## {label}\n")
            md.append("| Partenaire | Valeur |")
            md.append("|---|---|")
            for p in partners[:8]:
                md.append(f"| {p.get('label', 'N/A')} | {_fmt_usd(p.get('value', 0))} |")
            md.append("")

    # Market segmentation
    seg = fw.get("market_segmentation")
    if seg and seg.get("segments"):
        md.append("## Segmentation du marche\n")
        md.append("| Segment | Part | Taille | Croissance |")
        md.append("|---|---|---|---|")
        for s in seg["segments"]:
            md.append(f"| {s.get('name', '')} | {s.get('share_pct', 0)}% | {_fmt_usd(s.get('size_usd', 0))} | {s.get('growth', '')} |")
        if seg.get("summary"):
            md.append(f"\n> {seg['summary']}\n")

    # Leader companies
    leaders = fw.get("leader_companies", [])
    if leaders:
        md.append("## Entreprises leaders\n")
        md.append("| # | Entreprise | Pays | Part de marche |")
        md.append("|---|---|---|---|")
        for i, c in enumerate(leaders, 1):
            md.append(f"| {i} | {c.get('name', '')} | {c.get('country', '')} | {c.get('market_share_pct', 0)}% |")
        md.append("")

    # PESTEL
    pestel = fw.get("pestel")
    if pestel:
        md.append("## Analyse PESTEL\n")
        for key, label in [("political", "Politique"), ("economic", "Economique"), ("social", "Social"),
                           ("technological", "Technologique"), ("environmental", "Environnemental"), ("legal", "Legal")]:
            val = pestel.get(key)
            if val:
                md.append(f"### {label}\n{_render_val(val)}\n")
        if pestel.get("summary"):
            md.append(f"> **Synthese :** {pestel['summary']}\n")

    # TAM/SAM/SOM
    tam = fw.get("tam_sam_som")
    if tam:
        md.append("## Taille de marche — TAM / SAM / SOM\n")
        md.append("| Marche | Valeur | Description |")
        md.append("|---|---|---|")
        for k, label in [("tam", "TAM"), ("sam", "SAM"), ("som", "SOM")]:
            entry = tam.get(k)
            if entry:
                md.append(f"| {label} | {_fmt_usd(entry.get('value_usd', 0))} | {entry.get('description', '')} |")
        md.append("")
        if tam.get("methodology"):
            md.append(f"*Methodologie : {tam['methodology']}*\n")

    # Porter
    porter = fw.get("porter")
    if porter:
        md.append("## Forces de Porter\n")
        for key, label in [("rivalry", "Rivalite concurrentielle"), ("new_entrants", "Menace nouveaux entrants"),
                           ("substitutes", "Menace des substituts"), ("buyer_power", "Pouvoir des acheteurs"),
                           ("supplier_power", "Pouvoir des fournisseurs")]:
            val = porter.get(key)
            if val:
                md.append(f"### {label}\n{_render_val(val)}\n")
        if porter.get("summary"):
            md.append(f"> **Synthese :** {porter['summary']}\n")

    # BCG
    bcg = fw.get("bcg")
    if bcg:
        pos_labels = {"star": "Etoile", "cash_cow": "Vache a lait", "question_mark": "Dilemme", "dog": "Poids mort"}
        md.append("## Matrice BCG\n")
        md.append(f"**Position :** {pos_labels.get(bcg.get('position', ''), bcg.get('position', ''))}")
        md.append(f"\n- Part de marche relative : {bcg.get('x_market_share', 0) * 100:.1f}%")
        md.append(f"- Croissance du marche : {bcg.get('y_market_growth', 0) * 100:.1f}%")
        if bcg.get("justification"):
            md.append(f"\n> {bcg['justification']}\n")

    # Recommendations
    recs = fw.get("recommendations", [])
    if recs:
        md.append("## Recommandations strategiques\n")
        for i, r in enumerate(recs, 1):
            md.append(f"{i}. {r}")
        md.append("")

    # Strategic projection
    proj = fw.get("strategic_projection")
    if proj:
        md.append("## Projection strategique (3-5 ans)\n")
        md.append(f"{proj}\n")

    # News
    news = data.get("recent_news", [])
    if news:
        md.append("## Actualites recentes\n")
        for n in news[:8]:
            title = n.get("title", "")
            src = n.get("source_name", "")
            md.append(f"- **{title}** ({src})")
        md.append("")

    return "\n".join(md)


def _build_deep_analysis_email_html(title: str, markdown_content: str) -> str:
    """Convert deep analysis markdown to professional HTML email."""
    html = markdown_content

    # Tables
    def _convert_table(match):
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
    html = _re.sub(r"^> (.+)$", r'<div style="border-left:4px solid #3fa69c;padding:12px 16px;background:#f0faf9;margin:16px 0;border-radius:0 8px 8px 0;"><p style="margin:0;color:#353A3A;font-size:13px;">\1</p></div>', html, flags=_re.MULTILINE)
    # Headings
    html = _re.sub(r"^### (.+)$", r'<h3 style="color:#353A3A;font-size:15px;margin:20px 0 8px;font-weight:700;">\1</h3>', html, flags=_re.MULTILINE)
    html = _re.sub(r"^## (.+)$", r'<h2 style="color:#353A3A;font-size:17px;margin:24px 0 10px;border-bottom:2px solid #C1DEDB;padding-bottom:8px;font-weight:700;">\1</h2>', html, flags=_re.MULTILINE)
    html = _re.sub(r"^# (.+)$", r'<h1 style="color:#353A3A;font-size:20px;margin:28px 0 12px;font-weight:800;">\1</h1>', html, flags=_re.MULTILINE)
    # Bold & italic
    html = _re.sub(r"\*\*(.+?)\*\*", r"<strong style='color:#353A3A;'>\1</strong>", html)
    html = _re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    # HR
    html = _re.sub(r"^---+$", '<hr style="border:none;height:2px;background:linear-gradient(90deg,#3fa69c,#C1DEDB);margin:24px 0;">', html, flags=_re.MULTILINE)
    # Numbered lists
    html = _re.sub(r"^\d+\. (.+)$", r'<li style="margin:4px 0;color:#555e5e;">\1</li>', html, flags=_re.MULTILINE)
    # Bullet lists
    html = _re.sub(r"^- (.+)$", r'<li style="margin:4px 0;color:#555e5e;">\1</li>', html, flags=_re.MULTILINE)
    html = _re.sub(r"(<li[^>]*>.*</li>\n?)+", r'<ul style="padding-left:20px;margin:10px 0;">\g<0></ul>', html)
    # Paragraphs
    html = _re.sub(r"\n\n", '</p><p style="color:#555e5e;line-height:1.7;margin:10px 0;">', html)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%d/%m/%Y")

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
              Analyse Produit &middot; {date_str} &middot; Genere par IA
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
                    Cette analyse a ete generee automatiquement par la plateforme de veille CTTH.
                  </p>
                  <p style="margin:4px 0 0;font-size:11px;color:#8a9494;">
                    &copy; {now.year} CTTH &mdash; Centre Technique du Textile et de l'Habillement
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


def _build_deep_analysis_pdf_html(title: str, markdown_content: str) -> str:
    """Convert deep analysis markdown to printable HTML for WeasyPrint PDF."""
    import markdown as md_lib
    html_body = md_lib.markdown(markdown_content, extensions=["tables", "smarty"])
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    from jinja2 import Environment, FileSystemLoader
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("report_base.html")
    return template.render(title=title, content=html_body, generated_at=now)


@router.post("/deep-analysis/share")
async def share_deep_analysis(
    body: DeepAnalysisShareRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Send deep analysis results by email."""
    from app.services.product_analysis_service import run_deep_analysis

    # Run or get cached analysis
    data = await run_deep_analysis(db, body.hs_code, body.year)

    # Collect emails
    emails: list[str] = list(body.extra_emails)
    if body.recipient_ids:
        cursor = db.email_recipients.find({"_id": {"$in": body.recipient_ids}, "user_id": user["_id"]})
        saved = await cursor.to_list(100)
        for s in saved:
            if s.get("email") and s["email"] not in emails:
                emails.append(s["email"])

    if not emails:
        raise HTTPException(status_code=400, detail="Aucun destinataire specifie")

    # Build email
    hs_desc = data.get("hs_description", f"HS {body.hs_code}")
    title = f"Analyse Produit — {hs_desc} ({body.year})"
    markdown = _build_deep_analysis_markdown(data)
    html_email = _build_deep_analysis_email_html(title, markdown)
    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    subject = f"Rapport de veille stratégique CTTH - {now_str}"

    # Send
    results = []
    payload_base = {"cc": "", "bcc": "", "isHtml": True, "attachments": []}
    async with httpx.AsyncClient(timeout=30.0) as client:
        for email_addr in emails:
            payload = {**payload_base, "to": email_addr, "subject": subject, "message": html_email}
            sent = False
            last_error = ""
            for url in [settings.MAIL_API_URL, settings.MAIL_API_FALLBACK_URL]:
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        results.append({"email": email_addr, "status": "sent"})
                        sent = True
                        break
                    else:
                        last_error = f"HTTP {resp.status_code}"
                except Exception as exc:
                    last_error = str(exc)
            if not sent:
                results.append({"email": email_addr, "status": "error", "detail": last_error})

    sent_count = sum(1 for r in results if r["status"] == "sent")
    return {"total": len(emails), "sent": sent_count, "failed": len(emails) - sent_count, "results": results}


@router.post("/deep-analysis/pdf")
async def download_deep_analysis_pdf(
    body: DeepAnalysisRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Generate and return a PDF of the deep analysis."""
    from app.services.product_analysis_service import run_deep_analysis

    data = await run_deep_analysis(db, body.hs_code, body.year)
    hs_desc = data.get("hs_description", f"HS {body.hs_code}")
    title = f"Analyse Produit — {hs_desc} ({body.year})"
    markdown = _build_deep_analysis_markdown(data)

    # Build PDF HTML
    try:
        pdf_html = _build_deep_analysis_pdf_html(title, markdown)
    except Exception as e:
        logger.warning(f"PDF HTML template failed, using simple HTML: {e}")
        import markdown as md_lib
        pdf_html = f"<html><head><meta charset='utf-8'><title>{title}</title><style>body{{font-family:sans-serif;padding:40px;}}table{{width:100%;border-collapse:collapse;}}th,td{{padding:8px;border:1px solid #ddd;text-align:left;}}th{{background:#3fa69c;color:#fff;}}</style></head><body>{md_lib.markdown(markdown, extensions=['tables'])}</body></html>"

    # Generate PDF
    pdf_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_filename = f"deep_analysis_{body.hs_code}_{body.year}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    try:
        from weasyprint import HTML
        HTML(string=pdf_html).write_pdf(pdf_path)
    except ImportError:
        logger.warning("weasyprint not installed, generating simple text PDF")
        # Fallback: generate a minimal PDF with reportlab or just return error
        raise HTTPException(status_code=500, detail="WeasyPrint non installe. Installez avec: pip install weasyprint")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur generation PDF: {str(e)[:200]}")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"CTTH_Analyse_{body.hs_code}_{body.year}.pdf",
    )
