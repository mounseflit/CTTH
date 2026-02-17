"""
UN Comtrade Agent — Morocco textile trade data (HS chapters 50-63).

Uses the Comtrade v1 API:  https://comtradeapi.un.org/data/v1/get/C/A/HS
Subscription key is required (Ocp-Apim-Subscription-Key header).
Rate limit ≈ 500 calls/day.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timezone

from app.agents.base_agent import BaseAgent
from app.agents.constants import (
    GLOBAL_TOP_PARTNERS_M49,
    HS_CHAPTER_DESCRIPTIONS_FR,
    MOROCCO_M49,
    SOURCE_COMTRADE,
    TEXTILE_HS_CHAPTERS_STR,
)
from app.config import settings

_COMTRADE_BASE = "https://comtradeapi.un.org/data/v1/get/C/A/HS"


class ComtradeAgent(BaseAgent):
    source_name = SOURCE_COMTRADE

    def fetch_data(self, **kwargs) -> int:
        api_key = settings.COMTRADE_PRIMARY_KEY
        if not api_key:
            self.logger.error("No Comtrade API key configured")
            return 0

        calls = self.get_api_calls_today()
        if calls >= 480:
            self.logger.warning(f"Rate limit approaching: {calls}/500 calls today, skipping")
            return 0

        total = 0
        # 1) World totals by HS chapter
        try:
            total += self._fetch_world(api_key)
        except Exception as exc:
            self.logger.error(f"Comtrade world fetch error: {exc}")

        time.sleep(2)

        # 2) Per-partner breakdown
        try:
            total += self._fetch_partners(api_key)
        except Exception as exc:
            self.logger.error(f"Comtrade partner fetch error: {exc}")

        self.logger.info(f"Comtrade fetch complete: {total} records upserted")
        return total

    # ── world aggregates ─────────────────────────────────
    def _fetch_world(self, api_key: str) -> int:
        current_year = date.today().year
        periods = ",".join(str(y) for y in range(current_year - 4, current_year + 1))
        params = {
            "reporterCode": MOROCCO_M49,
            "cmdCode": TEXTILE_HS_CHAPTERS_STR,
            "flowCode": "M,X",
            "partnerCode": "0",
            "period": periods,
            "includeDesc": "true",
        }
        resp = self.safe_request(_COMTRADE_BASE, params=params, headers=self._auth(api_key))
        self.increment_api_calls()
        return self._parse_and_store(resp.json())

    # ── per-partner detail ───────────────────────────────
    def _fetch_partners(self, api_key: str) -> int:
        current_year = date.today().year
        periods = ",".join(str(y) for y in range(current_year - 3, current_year + 1))
        partner_codes = ",".join(k for k in GLOBAL_TOP_PARTNERS_M49 if k != "0")
        params = {
            "reporterCode": MOROCCO_M49,
            "cmdCode": TEXTILE_HS_CHAPTERS_STR,
            "flowCode": "M,X",
            "partnerCode": partner_codes,
            "period": periods,
            "includeDesc": "true",
        }
        resp = self.safe_request(_COMTRADE_BASE, params=params, headers=self._auth(api_key))
        self.increment_api_calls()
        return self._parse_and_store(resp.json())

    # ── parse + upsert ───────────────────────────────────
    def _parse_and_store(self, data: dict) -> int:
        records = data.get("data", [])
        if not records:
            self.logger.warning("No data in Comtrade response")
            return 0

        count = 0
        for rec in records:
            try:
                flow_code = rec.get("flowCode", "")
                if flow_code == "M":
                    flow = "import"
                elif flow_code == "X":
                    flow = "export"
                else:
                    continue

                cmd_code = str(rec.get("cmdCode", ""))
                period_date = self._parse_period(str(rec.get("period", "")))
                if period_date is None:
                    continue

                chapter = cmd_code[:2] if len(cmd_code) >= 2 else cmd_code
                reporter_code = str(rec.get("reporterCode", ""))
                partner_code = str(rec.get("partnerCode", ""))

                filt = {
                    "source": "comtrade",
                    "reporter_code": reporter_code,
                    "partner_code": partner_code,
                    "hs_code": cmd_code,
                    "flow": flow,
                    "period_date": datetime.combine(period_date, datetime.min.time()),
                    "frequency": "A",
                }
                primary_value = rec.get("primaryValue")
                net_wgt = rec.get("netWgt")
                qty = rec.get("qty")

                upd: dict = {
                    "reporter_name": rec.get("reporterDesc", ""),
                    "partner_name": rec.get("partnerDesc", ""),
                    "hs_description": HS_CHAPTER_DESCRIPTIONS_FR.get(chapter, rec.get("cmdDescE", "")),
                    "updated_at": datetime.now(timezone.utc),
                }
                if primary_value is not None:
                    upd["value_usd"] = float(primary_value)
                if net_wgt is not None:
                    upd["weight_kg"] = float(net_wgt)
                if qty is not None:
                    upd["quantity"] = float(qty)

                self.db.trade_data.update_one(
                    filt, {"$set": upd, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}}, upsert=True
                )
                count += 1
            except Exception as exc:
                self.logger.error(f"Error processing Comtrade record: {exc}")
        return count

    # ── helpers ──────────────────────────────────────────
    @staticmethod
    def _auth(api_key: str) -> dict:
        return {"Ocp-Apim-Subscription-Key": api_key}

    @staticmethod
    def _parse_period(period_str: str) -> date | None:
        try:
            if len(period_str) == 4:
                return date(int(period_str), 1, 1)
            if len(period_str) == 6:
                return date(int(period_str[:4]), int(period_str[4:]), 1)
            return None
        except (ValueError, IndexError):
            return None
