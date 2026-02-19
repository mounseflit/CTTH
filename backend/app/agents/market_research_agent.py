"""
Market Research Agent — AI-powered web search for competitive intelligence,
company profiles, market share, and segmentation data for the Moroccan
textile sector.

Uses the same dual-engine approach as GeneralWatcher:
  1. OpenAI  gpt-4o-search-preview  (web_search_options)
  2. Google  gemini-2.0-flash        (google_search tool)
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from openai import OpenAI

from app.agents.base_agent import BaseAgent
from app.config import settings
from app.models.market_research import (
    new_company_doc,
    new_competitive_event_doc,
    new_insight_doc,
    new_market_share_doc,
    new_segment_doc,
)

SOURCE_MARKET_RESEARCH = "market_research_agent"

# ── Search Queries ──────────────────────────────────────────

_COMPANY_QUERIES = [
    "Principales entreprises textiles Maroc exportation Europe 2024 2025 2026",
    "Top Moroccan textile manufacturers exporters apparel denim knitwear",
    "Entreprises confection habillement Maroc Casablanca Tanger chiffre affaires",
    "Morocco garment industry leading companies SWOT analysis",
]

_MARKET_SHARE_QUERIES = [
    "Parts de marche textile habillement Maroc 2024 2025",
    "Morocco textile market share breakdown by company segment",
    "Marche textile Maroc taille valeur croissance previsions",
]

_EVENT_QUERIES = [
    "Investissements usines textile Maroc 2024 2025 2026 nouvelles zones industrielles",
    "Morocco textile M&A partnerships joint ventures nearshoring",
    "Accords commerciaux textile Maroc Europe expansion usine",
]

_SEGMENT_QUERIES = [
    "Segmentation marche textile Maroc denim tricot tisse fibres",
    "Morocco textile product categories breakdown export import shares",
]

# ── System Prompts ──────────────────────────────────────────

_COMPANY_SYSTEM = (
    "Tu es un analyste specialise dans l'industrie textile marocaine. "
    "Recherche les principales entreprises du secteur textile et habillement au Maroc. "
    "Pour chaque entreprise trouvee, retourne un JSON strict avec:\n"
    '- "name": nom de l\'entreprise\n'
    '- "country": code pays ISO2 (ex: "MA")\n'
    '- "hq_city": ville du siege\n'
    '- "description_fr": description en 2-3 phrases en francais\n'
    '- "website": URL du site web\n'
    '- "swot": {"strengths": [...], "weaknesses": [...], "opportunities": [...], "threats": [...]}\n'
    '- "financials": {"revenue_usd": nombre ou null, "employees": nombre ou null, "year": annee}\n'
    '- "executives": [{"name": "...", "title": "..."}]\n\n'
    'Retourne un objet JSON avec une cle "companies" contenant un tableau. '
    "Maximum 5 resultats par recherche. UNIQUEMENT du JSON valide."
)

_EVENT_SYSTEM = (
    "Tu es un analyste specialise dans le secteur textile marocain. "
    "Recherche les evenements recents: investissements, M&A, partenariats, expansions. "
    "Pour chaque evenement, retourne un JSON strict avec:\n"
    '- "event_type": un parmi [m_and_a, partnership, expansion, regulation, investment]\n'
    '- "company_name": entreprise concernee\n'
    '- "title": titre de l\'evenement\n'
    '- "description_fr": description en 2-3 phrases\n'
    '- "event_date": date si disponible (YYYY-MM-DD)\n'
    '- "source_url": URL source\n'
    '- "source_name": nom du media\n\n'
    'Retourne un objet JSON avec une cle "events" contenant un tableau. '
    "Maximum 5 resultats. UNIQUEMENT du JSON valide."
)

_INSIGHT_SYSTEM = (
    "Tu es un consultant senior en strategie textile. "
    "A partir des resultats de recherche, identifie les tendances cles, risques, "
    "opportunites et defis pour le secteur textile marocain. "
    "Pour chaque insight, retourne un JSON strict avec:\n"
    '- "category": un parmi [trend, risk, opportunity, challenge, driver]\n'
    '- "title": titre court\n'
    '- "narrative_fr": analyse detaillee en 3-5 phrases en francais\n'
    '- "droc_type": un parmi [driver, restraint, opportunity, challenge]\n'
    '- "tags": liste de mots-cles\n\n'
    'Retourne un objet JSON avec une cle "insights" contenant un tableau. '
    "Maximum 5 resultats. UNIQUEMENT du JSON valide."
)


class MarketResearchAgent(BaseAgent):
    source_name = SOURCE_MARKET_RESEARCH

    def __init__(self, db):
        super().__init__(db)
        self._openai = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self._gemini_key = settings.GEMINI_API_KEY

    def fetch_data(self, **kwargs) -> int:
        total = 0

        # ── Companies ──────────────────────────────────────
        for query in _COMPANY_QUERIES:
            try:
                total += self._search_companies(query)
            except Exception as exc:
                self.logger.error(f"Company search error: {exc}")

        # ── Events ─────────────────────────────────────────
        for query in _EVENT_QUERIES:
            try:
                total += self._search_events(query)
            except Exception as exc:
                self.logger.error(f"Event search error: {exc}")

        # ── Insights from market share/segment queries ─────
        for query in _MARKET_SHARE_QUERIES + _SEGMENT_QUERIES:
            try:
                total += self._search_insights(query)
            except Exception as exc:
                self.logger.error(f"Insight search error: {exc}")

        self.logger.info(f"Market research agent complete: {total} new records")
        return total

    # ── Company search ─────────────────────────────────────

    def _search_companies(self, query: str) -> int:
        raw = self._ai_search(query, _COMPANY_SYSTEM)
        if not raw:
            return 0

        companies = self._parse_json(raw, "companies")
        count = 0
        for c in companies:
            name = c.get("name", "").strip()
            if not name:
                continue
            # Dedup
            if self.db.companies.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}}):
                continue

            swot = c.get("swot", {})
            if not isinstance(swot, dict):
                swot = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}

            doc = new_company_doc(
                name=name,
                country=c.get("country", "MA"),
                hq_city=c.get("hq_city", ""),
                description_fr=c.get("description_fr", ""),
                swot=swot,
                financials=c.get("financials") or {},
                executives=c.get("executives") or [],
                website=c.get("website", ""),
                source="ai_search",
            )
            try:
                self.db.companies.insert_one(doc)
                count += 1
            except Exception:
                pass
        return count

    # ── Event search ───────────────────────────────────────

    def _search_events(self, query: str) -> int:
        raw = self._ai_search(query, _EVENT_SYSTEM)
        if not raw:
            return 0

        events = self._parse_json(raw, "events")
        count = 0
        for e in events:
            title = e.get("title", "").strip()
            if not title:
                continue
            # Dedup
            if self.db.competitive_events.find_one({"title": title}):
                continue

            event_date = None
            if e.get("event_date"):
                try:
                    event_date = datetime.strptime(e["event_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass

            valid_types = {"m_and_a", "partnership", "expansion", "regulation", "investment"}
            event_type = e.get("event_type", "investment")
            if event_type not in valid_types:
                event_type = "investment"

            doc = new_competitive_event_doc(
                event_type=event_type,
                company_name=e.get("company_name", ""),
                title=title,
                description_fr=e.get("description_fr", ""),
                event_date=event_date,
                source_url=e.get("source_url", ""),
                source_name=e.get("source_name", ""),
            )
            try:
                self.db.competitive_events.insert_one(doc)
                count += 1
            except Exception:
                pass
        return count

    # ── Insight search ─────────────────────────────────────

    def _search_insights(self, query: str) -> int:
        raw = self._ai_search(query, _INSIGHT_SYSTEM)
        if not raw:
            return 0

        insights = self._parse_json(raw, "insights")
        count = 0
        for i in insights:
            title = i.get("title", "").strip()
            if not title:
                continue
            # Dedup by title
            if self.db.insights.find_one({"title": title}):
                continue

            valid_cats = {"trend", "risk", "opportunity", "challenge", "driver"}
            category = i.get("category", "trend")
            if category not in valid_cats:
                category = "trend"

            valid_droc = {"driver", "restraint", "opportunity", "challenge"}
            droc = i.get("droc_type")
            if droc and droc not in valid_droc:
                droc = None

            doc = new_insight_doc(
                category=category,
                title=title,
                narrative_fr=i.get("narrative_fr", ""),
                droc_type=droc,
                tags=i.get("tags", []),
            )
            try:
                self.db.insights.insert_one(doc)
                count += 1
            except Exception:
                pass
        return count

    # ── AI Search (OpenAI or Gemini) ───────────────────────

    def _ai_search(self, query: str, system_prompt: str) -> str:
        """Try OpenAI first, fall back to Gemini."""
        if self._openai:
            try:
                resp = self._openai.chat.completions.create(
                    model="gpt-4o-search-preview",
                    web_search_options={"search_context_size": "medium"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                    ],
                )
                self.increment_api_calls()
                return resp.choices[0].message.content or ""
            except Exception as exc:
                self.logger.warning(f"OpenAI search failed, trying Gemini: {exc}")

        if self._gemini_key:
            try:
                return self._gemini_search(query, system_prompt)
            except Exception as exc:
                self.logger.error(f"Gemini search also failed: {exc}")

        return ""

    def _gemini_search(self, query: str, system_prompt: str) -> str:
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self._gemini_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\nRecherche: {query}"}]},
            ],
            "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
        }

        resp = httpx.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        self.increment_api_calls()

        body = resp.json()
        candidates = body.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return " ".join(p.get("text", "") for p in parts if "text" in p)

    # ── JSON Parsing ───────────────────────────────────────

    def _parse_json(self, raw: str, key: str) -> list:
        """Parse JSON from LLM response, extracting array from given key."""
        content = raw.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

        try:
            return json.loads(content).get(key, [])
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(content[start:end]).get(key, [])
                except json.JSONDecodeError:
                    pass
            self.logger.warning(f"Could not parse JSON for key '{key}'")
            return []
