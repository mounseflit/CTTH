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
        report_type = report.get("report_type", "custom")

        # Step 1: Gather data from MongoDB
        if report_type == "market_research":
            data_context = self._gather_market_research_data(params)
        else:
            data_context = self._gather_data(params)

        # Step 2: Generate narrative with LLM
        custom_prompt = params.get("custom_prompt", "") if report_type == "custom" else ""
        markdown_content = self._generate_narrative(report_type, data_context, custom_prompt=custom_prompt)

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
    # Market research data gathering
    # ------------------------------------------------------------------

    def _gather_market_research_data(self, params: dict) -> dict:
        """Build comprehensive market research data context."""
        # Start with base trade data
        context = self._gather_data(params)

        # Add market segments
        segments = list(self.db.market_segments.find({}).limit(30))
        context["market_segments"] = [
            {"axis": s.get("axis", ""), "code": s.get("code", ""), "label_fr": s.get("label_fr", "")}
            for s in segments
        ]

        # Add market size series (latest years)
        size_data = list(
            self.db.market_size_series.find({"segment_code": "ALL"}).sort("year", -1).limit(10)
        )
        context["market_size_trend"] = [
            {"year": d.get("year"), "flow": d.get("flow", ""), "value_usd": d.get("value_usd", 0)}
            for d in size_data
        ]

        # Add companies
        companies = list(self.db.companies.find({}).sort("name", 1).limit(20))
        context["companies"] = [
            {
                "name": c.get("name", ""),
                "country": c.get("country", ""),
                "description_fr": c.get("description_fr", ""),
                "swot": c.get("swot", {}),
                "financials": c.get("financials", {}),
            }
            for c in companies
        ]

        # Add market share
        share_data = list(self.db.market_share_series.find({}).sort("share_pct", -1).limit(20))
        context["market_share"] = [
            {"company_name": d.get("company_name", ""), "share_pct": d.get("share_pct", 0), "year": d.get("year")}
            for d in share_data
        ]

        # Add competitive events
        events = list(self.db.competitive_events.find({}).sort("event_date", -1).limit(15))
        context["competitive_events"] = [
            {
                "event_type": e.get("event_type", ""),
                "company_name": e.get("company_name", ""),
                "title": e.get("title", ""),
                "description_fr": e.get("description_fr", ""),
                "event_date": str(e.get("event_date", ""))[:10],
            }
            for e in events
        ]

        # Add insights
        insights = list(self.db.insights.find({}).sort("created_at", -1).limit(10))
        context["insights"] = [
            {
                "category": i.get("category", ""),
                "title": i.get("title", ""),
                "narrative_fr": i.get("narrative_fr", ""),
                "droc_type": i.get("droc_type"),
            }
            for i in insights
        ]

        return context

    # ------------------------------------------------------------------
    # LLM narrative
    # ------------------------------------------------------------------

    def _generate_narrative(self, report_type: str, context: dict, *, custom_prompt: str = "") -> str:
        """Generate French narrative using GPT-4o."""
        system_prompt = (
            "Tu es un analyste expert en commerce international textile pour le Maroc. "
            "Tu rediges un rapport professionnel en francais pour le CTTH "
            "(Centre Technique du Textile et de l'Habillement). "
            "\n\nREGLES IMPORTANTES:\n"
            "- Utilise UNIQUEMENT les chiffres fournis dans les donnees ci-dessous.\n"
            "- Ne genere JAMAIS de statistiques ou de chiffres inventes.\n"
            "- Si une donnee manque, indique 'Donnee non disponible'.\n"
            "\n\nREGLES DE MISE EN FORME MARKDOWN:\n"
            "- Utilise ## pour les titres de section et ### pour les sous-sections\n"
            "- Utilise des tableaux markdown (avec | separateurs) pour presenter les donnees chiffrees et comparaisons\n"
            "- Mets en **gras** les chiffres cles, pourcentages et termes importants\n"
            "- Utilise des listes a puces (-) pour les insights et listes numerotees (1.) pour les recommandations\n"
            "- Ajoute --- (ligne horizontale) entre les sections majeures\n"
            "- Utilise > (blockquote) pour les points cles et resumes de section\n"
            "- Formate les valeurs monetaires avec $ et separateurs de milliers (ex: $1.2B, $45.3M)\n"
            "- Chaque section doit avoir un contenu substantiel (minimum 3-4 paragraphes ou sous-sections)\n"
            "- Fournis des analyses de tendances et des recommandations strategiques."
        )

        data_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)

        if report_type == "custom" and custom_prompt:
            user_prompt = f"""
L'utilisateur a demande un rapport personnalise sur le sujet suivant :
"{custom_prompt}"

Donnees disponibles dans la base de donnees CTTH :
Periode: {context.get('period', 'Non specifiee')}

{data_str}

Redige un rapport complet, professionnel et detaille en francais sur le sujet demande.
Appuie-toi sur les donnees fournies ci-dessus pour enrichir ton analyse avec des chiffres reels.
Structure le rapport avec les sections suivantes (adapte les titres au sujet) :

1. **Resume Executif** - Points cles en 3-5 puces. Commence par un blockquote resumant la conclusion principale.
2. **Contexte et Enjeux** - Presentation du sujet et de son importance pour le secteur textile marocain.
3. **Analyse des Donnees** - Tableaux et analyses chiffrees en lien avec le sujet.
4. **Tendances et Perspectives** - Evolution recente et projections futures.
5. **Impact sur le Secteur Textile Marocain** - Consequences et opportunites pour le CTTH et les entreprises locales.
6. **Recommandations Strategiques** - Actions concretes numerotees, opportunites et risques.
"""
        elif report_type == "market_research":
            user_prompt = f"""
Donnees pour l'etude de marche complete:
Periode: {context.get('period', 'Non specifiee')}

{data_str}

Redige une etude de marche complete et detaillee en francais avec les 8 modules suivants.
Chaque section doit etre riche, avec des tableaux comparatifs, des analyses detaillees et des insights actionables.

1. **Resume Executif** - Points cles en 5-7 puces couvrant toutes les dimensions. Commence par un blockquote (>) resumant la conclusion principale.
2. **Vue d'Ensemble du Marche** - Taille du marche, croissance, TAM/SAM/SOM. Inclus un tableau recapitulatif des KPIs.
3. **Analyse de Segmentation** - Tableau de repartition par chapitre SH avec valeurs. Categories de produits et types de fibres.
4. **Paysage Concurrentiel (Forces de Porter)** - Analyse des 5 forces avec score (Faible/Moyen/Fort) pour chacune. Utilise un tableau.
5. **Analyse PESTEL** - Tableau des 6 dimensions avec facteurs cles et impact pour chacune.
6. **Profils d'Entreprises & Parts de Marche** - Tableau des entreprises cles avec pays, positionnement, part de marche estimee.
7. **Analyse des Flux Commerciaux** - Tableau exportations/importations/balance. Top partenaires avec volumes.
8. **Recommandations Strategiques** - Liste numerotee d'actions concretes. Opportunites, risques, et plan d'action.
"""
        else:
            user_prompt = f"""
Donnees pour le rapport de type "{report_type}":
Periode: {context.get('period', 'Non specifiee')}

{data_str}

Redige un rapport complet et bien structure en francais avec les sections suivantes.
Utilise des tableaux pour les donnees chiffrees et des blockquotes pour les points cles.

1. **Resume Executif** - Points cles en 3-5 puces. Commence par un blockquote resumant la conclusion principale.
2. **Analyse des Flux Commerciaux** - Tableau exportations/importations/balance avec comparaison.
3. **Principaux Partenaires Commerciaux** - Tableau par pays avec volumes et tendances.
4. **Analyse par Produit (Chapitre SH)** - Tableau de repartition sectorielle avec valeurs.
5. **Tendances et Evolution** - Analyse des tendances mensuelles avec interpretation.
6. **Contexte Reglementaire et Actualites** - Resume des actualites pertinentes par categorie.
7. **Recommandations Strategiques** - Liste numerotee d'opportunites et risques identifies.
"""

        response = self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=6000,
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
