"""
Federal Register Agent — US regulatory news on textile trade.

Uses the free Federal Register REST API (no key needed):
  https://www.federalregister.gov/api/v1/documents.json

Stores results as news_articles in MongoDB.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from openai import OpenAI

from app.agents.base_agent import BaseAgent
from app.agents.constants import SOURCE_FEDERAL_REGISTER
from app.config import settings

_FR_BASE = "https://www.federalregister.gov/api/v1"


class FederalRegisterAgent(BaseAgent):
    source_name = SOURCE_FEDERAL_REGISTER

    def __init__(self, db):
        super().__init__(db)
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    def fetch_data(self, **kwargs) -> int:
        total = 0
        try:
            total += self._fetch_textile_docs()
        except Exception as exc:
            self.logger.error(f"FR textile docs error: {exc}")
        try:
            total += self._fetch_morocco_docs()
        except Exception as exc:
            self.logger.error(f"FR Morocco docs error: {exc}")
        self.logger.info(f"Federal Register fetch complete: {total} new articles")
        return total

    def _fetch_textile_docs(self) -> int:
        since = (date.today() - timedelta(days=60)).isoformat()
        params = {
            "conditions[term]": "textile trade apparel import quota tariff",
            "conditions[publication_date][gte]": since,
            "conditions[type][]": ["RULE", "PRORULE", "NOTICE"],
            "fields[]": [
                "title", "abstract", "document_number",
                "html_url", "publication_date", "type", "agencies",
            ],
            "per_page": 50,
            "order": "newest",
        }
        resp = self.safe_request(f"{_FR_BASE}/documents.json", params=params)
        self.increment_api_calls()
        return self._store_results(resp.json().get("results", []))

    def _fetch_morocco_docs(self) -> int:
        since = (date.today() - timedelta(days=90)).isoformat()
        params = {
            "conditions[term]": "Morocco textile apparel trade antidumping",
            "conditions[publication_date][gte]": since,
            "fields[]": [
                "title", "abstract", "document_number",
                "html_url", "publication_date", "type", "agencies",
            ],
            "per_page": 25,
            "order": "newest",
        }
        resp = self.safe_request(f"{_FR_BASE}/documents.json", params=params)
        self.increment_api_calls()
        return self._store_results(resp.json().get("results", []))

    def _store_results(self, results: list) -> int:
        count = 0
        for doc in results:
            src_url = doc.get("html_url", "")
            if not src_url:
                continue
            if self.db.news_articles.find_one({"source_url": src_url}):
                continue

            title = doc.get("title", "")
            abstract = doc.get("abstract", "") or ""
            pub_date = doc.get("publication_date", "")

            summary = self._ai_summary(title, abstract) if self.openai else (abstract[:500] or title)

            agencies = doc.get("agencies", [])
            tags = [a.get("name", "") for a in agencies if isinstance(a, dict) and a.get("name")]
            tags.extend(["textile", "etats-unis", "reglementation"])

            pub_at = None
            if pub_date:
                try:
                    pub_at = datetime.strptime(pub_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    pass

            try:
                self.db.news_articles.insert_one({
                    "_id": str(uuid.uuid4()),
                    "title": title,
                    "summary": summary,
                    "content": abstract,
                    "source_url": src_url,
                    "source_name": "Federal Register",
                    "category": "regulatory",
                    "tags": tags,
                    "published_at": pub_at,
                    "relevance_score": 0.7,
                    "created_at": datetime.now(timezone.utc),
                })
                count += 1
            except Exception:
                pass
        return count

    def _ai_summary(self, title: str, abstract: str) -> str:
        try:
            resp = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un analyste spécialisé en commerce international textile. "
                            "Résume le document réglementaire suivant en français, en 2-3 phrases. "
                            "Concentre-toi sur l'impact pour le secteur textile marocain."
                        ),
                    },
                    {"role": "user", "content": f"Titre: {title}\n\nRésumé: {abstract or 'Non disponible'}"},
                ],
                max_tokens=300,
                temperature=0.3,
            )
            return resp.choices[0].message.content or abstract or title
        except Exception as exc:
            self.logger.warning(f"OpenAI summary failed: {exc}")
            return abstract or title
