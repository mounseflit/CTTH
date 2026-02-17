"""
General Watcher — AI-powered web search agent that combines OpenAI Search
Preview and Google Gemini to discover the latest news, trends & regulatory
changes affecting the Moroccan textile sector.

Uses two complementary LLM search engines:
  1. OpenAI  gpt-4o-search-preview  (web_search_options)
  2. Google  gemini-2.0-flash        (google_search tool)

Each engine runs a set of curated search queries and stores deduplicated
news articles in the news_articles collection.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from openai import OpenAI

from app.agents.base_agent import BaseAgent
from app.agents.constants import SOURCE_GENERAL_WATCHER
from app.config import settings

_SEARCH_QUERIES = [
    "Actualités secteur textile habillement Maroc exportations 2025 2026",
    "Accords commerciaux textile Maroc Union Européenne nearshoring",
    "Réglementation importation textile durabilité CBAM Union Européenne",
    "Marché mondial textile tendances prix coton fibres synthétiques 2026",
    "Concurrence textile Maroc Turquie Bangladesh Vietnam",
    "OTEXA US textile import data Morocco apparel trade 2025 2026",
    "Eurostat EU Morocco textile trade statistics latest",
]

_SYSTEM_PROMPT = (
    "Tu es un analyste spécialisé dans le commerce international du textile "
    "et de l'habillement, avec un focus sur le Maroc.\n"
    "Recherche les actualités les plus récentes et retourne les résultats au "
    "format JSON strict. Pour chaque résultat pertinent, fournis:\n"
    '- "title": titre de l\'article\n'
    '- "summary": résumé en 2-3 phrases en français\n'
    '- "source_url": URL de la source\n'
    '- "source_name": nom du média/source\n'
    '- "category": une parmi [regulatory, market, policy, trade_agreement, industry, sustainability, technology]\n'
    '- "tags": liste de mots-clés pertinents\n'
    '- "published_date": date si disponible (format YYYY-MM-DD)\n'
    '- "relevance_score": score de pertinence 0.0-1.0 pour le secteur textile marocain\n\n'
    'Retourne un objet JSON avec une clé "articles" contenant un tableau. '
    "Maximum 5 résultats par recherche. Retourne UNIQUEMENT du JSON valide."
)


class GeneralWatcher(BaseAgent):
    source_name = SOURCE_GENERAL_WATCHER

    def __init__(self, db):
        super().__init__(db)
        self._openai = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self._gemini_key = settings.GEMINI_API_KEY

    # ── public entry point ────────────────────────────────
    def fetch_data(self, **kwargs) -> int:
        total = 0

        # ── OpenAI Search Preview ─────────────────────────
        if self._openai:
            for query in _SEARCH_QUERIES:
                try:
                    total += self._openai_search(query)
                except Exception as exc:
                    self.logger.error(f"OpenAI search error for '{query[:40]}…': {exc}")

        # ── Gemini Search ─────────────────────────────────
        if self._gemini_key:
            for query in _SEARCH_QUERIES:
                try:
                    total += self._gemini_search(query)
                except Exception as exc:
                    self.logger.error(f"Gemini search error for '{query[:40]}…': {exc}")

        self.logger.info(f"General watcher complete: {total} new articles stored")
        return total

    # ── OpenAI gpt-4o-search-preview ─────────────────────
    def _openai_search(self, query: str) -> int:
        resp = self._openai.chat.completions.create(
            model="gpt-4o-search-preview",
            web_search_options={"search_context_size": "medium"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
        )
        self.increment_api_calls()
        return self._parse_and_store(resp.choices[0].message.content or "", "openai")

    # ── Google Gemini with google_search tool ─────────────
    def _gemini_search(self, query: str) -> int:
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self._gemini_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{_SYSTEM_PROMPT}\n\nRecherche: {query}"}]},
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
            return 0
        parts = candidates[0].get("content", {}).get("parts", [])
        text = " ".join(p.get("text", "") for p in parts if "text" in p)
        return self._parse_and_store(text, "gemini")

    # ── parse JSON + dedup + insert ──────────────────────
    def _parse_and_store(self, raw: str, engine: str) -> int:
        # Strip markdown code fences
        content = raw.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

        try:
            articles = json.loads(content).get("articles", [])
        except json.JSONDecodeError:
            # Try to extract JSON from mixed text
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    articles = json.loads(content[start:end]).get("articles", [])
                except json.JSONDecodeError:
                    self.logger.warning(f"[{engine}] Could not parse response as JSON")
                    return 0
            else:
                self.logger.warning(f"[{engine}] No JSON found in response")
                return 0

        count = 0
        for ad in articles:
            src_url = ad.get("source_url", "")
            title = ad.get("title", "")
            if not title:
                continue
            # Dedup by URL or title
            if src_url and self.db.news_articles.find_one({"source_url": src_url}):
                continue
            if not src_url and self.db.news_articles.find_one({"title": title}):
                continue

            pub_at = None
            if ad.get("published_date"):
                try:
                    pub_at = datetime.strptime(ad["published_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            if pub_at is None:
                pub_at = datetime.now(timezone.utc)

            cat = ad.get("category", "industry")
            valid_cats = {"regulatory", "market", "policy", "trade_agreement", "industry", "sustainability", "technology"}
            if cat not in valid_cats:
                cat = "industry"

            try:
                self.db.news_articles.insert_one({
                    "_id": str(uuid.uuid4()),
                    "title": title,
                    "summary": ad.get("summary", ""),
                    "source_url": src_url or f"ai-search://{engine}/{uuid.uuid4().hex[:8]}",
                    "source_name": ad.get("source_name", f"Veille IA ({engine})"),
                    "category": cat,
                    "tags": ad.get("tags", []),
                    "published_at": pub_at,
                    "relevance_score": float(ad.get("relevance_score", 0.5)),
                    "created_at": datetime.now(timezone.utc),
                })
                count += 1
            except Exception:
                pass
        return count
