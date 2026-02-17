import json
import logging
import os
from datetime import date, datetime, timezone

import markdown
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from pymongo.database import Database

from app.agents.constants import (
    HS_CHAPTER_DESCRIPTIONS_FR,
)
from app.config import settings

logger = logging.getLogger(__name__)

# Resolve template directory relative to this file (works both locally and in Docker)
_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


class ReportGenerationService:
    def __init__(self, db: Database):
        self.db = db
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.jinja_env = Environment(
            loader=FileSystemLoader(_TEMPLATE_DIR)
        )

    def generate(self, report: dict) -> dict:
        """Full report generation pipeline: MongoDB -> data -> LLM -> PDF.

        Returns a dict with content_markdown, content_html, pdf_path.
        """
        params = report.get("parameters") or {}

        # Step 1: Gather data from MongoDB
        data_context = self._gather_data(params)

        # Step 2: Generate narrative with LLM
        markdown_content = self._generate_narrative(
            report.get("report_type", "custom"), data_context
        )

        # Step 3: Render to HTML
        html_content = self._render_html(markdown_content, report.get("title", "Rapport"))

        # Step 4: Generate PDF (best-effort)
        pdf_path = None
        try:
            pdf_path = self._generate_pdf(html_content, str(report["_id"]))
        except Exception as exc:
            logger.warning(f"PDF generation skipped: {exc}")

        return {
            "content_markdown": markdown_content,
            "content_html": html_content,
            "pdf_path": pdf_path,
        }

    # ------------------------------------------------------------------
    # Data gathering via MongoDB aggregation
    # ------------------------------------------------------------------

    def _gather_data(self, params: dict) -> dict:
        """Build structured data context from MongoDB."""
        date_from_str = params.get("date_from", "2023-01-01")
        date_to_str = params.get("date_to", date.today().isoformat())

        date_from = datetime.fromisoformat(date_from_str)
        date_to = datetime.fromisoformat(date_to_str)

        context: dict = {}

        # Trade totals by flow
        pipeline = [
            {"$match": {"period_date": {"$gte": date_from, "$lte": date_to}}},
            {
                "$group": {
                    "_id": "$flow",
                    "total_usd": {"$sum": {"$ifNull": ["$value_usd", 0]}},
                    "total_eur": {"$sum": {"$ifNull": ["$value_eur", 0]}},
                    "total_weight": {"$sum": {"$ifNull": ["$weight_kg", 0]}},
                }
            },
        ]
        context["trade_totals"] = [
            {"flow": r["_id"], "total_usd": r["total_usd"], "total_eur": r["total_eur"], "total_weight": r["total_weight"]}
            for r in self.db.trade_data.aggregate(pipeline)
        ]

        # Top partners
        pipeline = [
            {"$match": {"period_date": {"$gte": date_from, "$lte": date_to}, "partner_code": {"$ne": "0"}}},
            {
                "$group": {
                    "_id": {"partner_name": "$partner_name", "flow": "$flow"},
                    "total_value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
                }
            },
            {"$sort": {"total_value": -1}},
            {"$limit": 20},
        ]
        context["top_partners"] = [
            {"partner_name": r["_id"]["partner_name"], "flow": r["_id"]["flow"], "total_value": r["total_value"]}
            for r in self.db.trade_data.aggregate(pipeline)
        ]

        # Monthly trends
        pipeline = [
            {"$match": {"period_date": {"$gte": date_from, "$lte": date_to}}},
            {
                "$group": {
                    "_id": {
                        "month": {"$dateToString": {"format": "%Y-%m", "date": "$period_date"}},
                        "flow": "$flow",
                    },
                    "value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
                }
            },
            {"$sort": {"_id.month": 1}},
        ]
        context["monthly_trends"] = [
            {"month": r["_id"]["month"], "flow": r["_id"]["flow"], "value": r["value"]}
            for r in self.db.trade_data.aggregate(pipeline)
        ]

        # HS breakdown
        pipeline = [
            {"$match": {"period_date": {"$gte": date_from, "$lte": date_to}}},
            {
                "$group": {
                    "_id": {"$substr": ["$hs_code", 0, 2]},
                    "total_value": {"$sum": {"$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]}},
                }
            },
            {"$sort": {"total_value": -1}},
        ]
        hs_data = []
        for r in self.db.trade_data.aggregate(pipeline):
            chapter = str(r["_id"] or "")
            hs_data.append({
                "chapter": chapter,
                "total_value": r["total_value"],
                "description_fr": HS_CHAPTER_DESCRIPTIONS_FR.get(chapter, ""),
            })
        context["hs_breakdown"] = hs_data

        # Recent news
        news = list(
            self.db.news_articles.find(
                {"published_at": {"$gte": date_from}},
                {"title": 1, "summary": 1, "category": 1, "source_name": 1, "published_at": 1},
            )
            .sort("relevance_score", -1)
            .limit(15)
        )
        context["recent_news"] = [
            {
                "title": n.get("title", ""),
                "summary": n.get("summary", ""),
                "category": n.get("category", ""),
                "source_name": n.get("source_name", ""),
                "published_date": str(n.get("published_at", ""))[:10],
            }
            for n in news
        ]

        context["period"] = f"{date_from_str} - {date_to_str}"
        return context

    # ------------------------------------------------------------------
    # LLM narrative
    # ------------------------------------------------------------------

    def _generate_narrative(self, report_type: str, context: dict) -> str:
        """Generate French narrative using GPT-4o."""
        system_prompt = (
            "Tu es un analyste expert en commerce international textile pour le Maroc. "
            "Tu rediges un rapport professionnel en francais pour le CTTH "
            "(Centre Technique du Textile et de l'Habillement). "
            "\n\nREGLES IMPORTANTES:\n"
            "- Utilise UNIQUEMENT les chiffres fournis dans les donnees ci-dessous.\n"
            "- Ne genere JAMAIS de statistiques ou de chiffres inventes.\n"
            "- Si une donnee manque, indique 'Donnee non disponible'.\n"
            "- Utilise le format markdown pour la mise en forme.\n"
            "- Structure le rapport avec des sections claires.\n"
            "- Fournis des analyses de tendances et des recommandations strategiques."
        )

        data_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)

        user_prompt = f"""
Donnees pour le rapport de type "{report_type}":
Periode: {context.get('period', 'Non specifiee')}

{data_str}

Redige un rapport complet en francais avec les sections suivantes:
1. **Resume Executif** - Points cles en 3-5 puces
2. **Analyse des Flux Commerciaux** - Exportations, importations, balance
3. **Principaux Partenaires Commerciaux** - Analyse par pays
4. **Analyse par Produit (Chapitre SH)** - Repartition sectorielle
5. **Tendances et Evolution** - Analyse des tendances mensuelles
6. **Contexte Reglementaire et Actualites** - Resume des actualites pertinentes
7. **Recommandations Strategiques** - Opportunites et risques identifies
"""

        response = self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=4000,
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    def _render_html(self, markdown_content: str, title: str) -> str:
        """Convert markdown to HTML using Jinja2 template."""
        html_body = markdown.markdown(
            markdown_content,
            extensions=["tables", "fenced_code"],
        )

        template = self.jinja_env.get_template("report_base.html")
        return template.render(
            title=title,
            content=html_body,
            generated_at=datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
        )

    def _generate_pdf(self, html_content: str, report_id: str) -> str:
        """Generate PDF from HTML (requires weasyprint)."""
        from weasyprint import HTML

        reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        pdf_path = os.path.join(reports_dir, f"{report_id}.pdf")
        HTML(string=html_content).write_pdf(pdf_path)
        return pdf_path
