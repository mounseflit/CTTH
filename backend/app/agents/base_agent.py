import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx
from pymongo.database import Database


class BaseAgent(ABC):
    source_name: str = ""

    def __init__(self, db: Database):
        self.db = db
        self.client = httpx.Client(timeout=60.0)
        self.logger = logging.getLogger(f"agent.{self.source_name}")

    @abstractmethod
    def fetch_data(self, **kwargs) -> int:
        pass

    def update_status(self, status: str, error_msg: str | None = None, records: int = 0):
        now = datetime.now(timezone.utc)
        update_fields: dict = {"status": status, "updated_at": now}
        if status == "active":
            update_fields["last_successful_fetch"] = now
            update_fields["last_error_message"] = None
        elif error_msg:
            update_fields["last_error_message"] = error_msg

        self.db.data_source_status.update_one(
            {"source_name": self.source_name},
            {"$set": update_fields, "$inc": {"records_fetched_today": records},
             "$setOnInsert": {"source_name": self.source_name, "api_calls_today": 0}},
            upsert=True,
        )

    def increment_api_calls(self, count: int = 1):
        self.db.data_source_status.update_one(
            {"source_name": self.source_name},
            {"$inc": {"api_calls_today": count}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        )

    def get_api_calls_today(self) -> int:
        doc = self.db.data_source_status.find_one({"source_name": self.source_name}, {"api_calls_today": 1})
        return doc.get("api_calls_today", 0) if doc else 0

    def safe_request(self, url: str, params: dict | None = None, headers: dict | None = None, max_retries: int = 3) -> httpx.Response:
        for attempt in range(max_retries):
            try:
                response = self.client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait = 2 ** (attempt + 1) * 10
                    self.logger.warning(f"Rate limited, waiting {wait}s (attempt {attempt + 1})")
                    time.sleep(wait)
                elif e.response.status_code >= 500:
                    wait = 2 ** attempt * 5
                    self.logger.warning(f"Server error {e.response.status_code}, retrying in {wait}s")
                    time.sleep(wait)
                else:
                    raise
            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt * 5
                    self.logger.warning(f"Request error: {e}, retrying in {wait}s")
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError(f"Failed after {max_retries} retries: {url}")

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass
