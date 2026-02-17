"""
OTEXA / trade.gov Agent — US textile trade data & news from OTEXA, Federal
Register, and the trade.gov public pages.

Scrapes OTEXA public trade-data pages and the trade.gov news feed using
OpenAI web_search_preview to extract structured data.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from openai import OpenAI

from app.agents.base_agent import BaseAgent
from app.agents.constants import SOURCE_OTEXA
from app.config import settings

_OTEXA_URLS = [
    "https://www.trade.gov/otexa-trade-data-page",
    "https://www.trade.gov/trade-news-and-events",
]


class OtexaAgent(BaseAgent):
    source_name = SOURCE_OTEXA

    def __init__(self, db):
        super().__init__(db)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)

    def fetch_data(self, **kwargs) -> int:
        total = 0
        try:
            total += self._fetch_trade_news()
        except Exception as exc:
            self.logger.error(f"OTEXA news fetch error: {exc}")
        try:
            total += self._fetch_trade_data_insights()
        except Exception as exc:
            self.logger.error(f"OTEXA data fetch error: {exc}")
        self.logger.info(f"OTEXA fetch complete: {total} records")
        return total

    # ── trade news from trade.gov ────────────────────────
    def _fetch_trade_news(self) -> int:
        prompt = (
            "Search the website https://www.trade.gov for the latest textile and apparel "
            "trade news, regulations, and updates related to Morocco or North Africa. "
            "Also check https://www.trade.gov/otexa-trade-data-page for any recent data releases. "
            "Return a JSON object with key 'articles' containing an array of up to 8 articles. "
            "Each article must have: title, summary (2-3 sentences in French), source_url, "
            "source_name, category (one of: regulatory, market, policy, trade_agreement, industry), "
            "tags (array of keywords), published_date (YYYY-MM-DD if known), "
            "relevance_score (0.0-1.0 for Morocco textile sector relevance)."
        )
        return self._search_and_store(prompt)

    # ── data insights via web search ─────────────────────
    def _fetch_trade_data_insights(self) -> int:
        prompt = (
            "Search OTEXA (https://www.trade.gov/otexa) and US trade regulation sites for "
            "the latest US textile import/export data, quotas, tariff changes, and anti-dumping "
            "measures affecting Morocco or the Maghreb region. "
            "Return a JSON object with key 'articles' containing up to 5 results. "
            "Each must have: title, summary (in French), source_url, source_name, "
            "category, tags, published_date, relevance_score."
        )
        return self._search_and_store(prompt)

    # ── common OpenAI web search → MongoDB ───────────────
    def _search_and_store(self, prompt: str) -> int:
        try:
            resp = self.openai.chat.completions.create(
                model="gpt-4o-search-preview",
                web_search_options={"search_context_size": "medium"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un analyste spécialisé dans le commerce international du textile. "
                            "Effectue une recherche web et retourne les résultats au format JSON strict. "
                            "Retourne UNIQUEMENT un JSON valide sans texte autour."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:
            self.logger.error(f"OpenAI search call failed: {exc}")
            return 0

        self.increment_api_calls()
        content = resp.choices[0].message.content or ""

        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

        try:
            articles = json.loads(content).get("articles", [])
        except json.JSONDecodeError:
            self.logger.error("Failed to parse OTEXA search result as JSON")
            return 0

        count = 0
        for ad in articles:
            src_url = ad.get("source_url", "")
            if not src_url or self.db.news_articles.find_one({"source_url": src_url}):
                continue

            pub_at = None
            if ad.get("published_date"):
                try:
                    pub_at = datetime.strptime(ad["published_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            if pub_at is None:
                pub_at = datetime.now(timezone.utc)

            try:
                self.db.news_articles.insert_one({
                    "_id": str(uuid.uuid4()),
                    "title": ad.get("title", ""),
                    "summary": ad.get("summary", ""),
                    "source_url": src_url,
                    "source_name": ad.get("source_name", "OTEXA / trade.gov"),
                    "category": ad.get("category", "regulatory"),
                    "tags": ad.get("tags", []) + ["otexa", "etats-unis"],
                    "published_at": pub_at,
                    "relevance_score": float(ad.get("relevance_score", 0.6)),
                    "created_at": datetime.now(timezone.utc),
                })
                count += 1
            except Exception:
                pass
        return count
