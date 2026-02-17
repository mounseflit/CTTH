"""
Eurostat Agent — EU ↔ Morocco trade data via the Eurostat JSON Statistics API.

Working datasets (confirmed Feb 2026):
  • ext_lt_maineu   – EU trade by SITC06 broad categories, annual

The old Comext DS-059322 HS-level endpoint no longer resolves.  We use
the macro-level Eurostat datasets for EU-wide totals and complement with
HS-level detail from the UN Comtrade agent.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timezone

from app.agents.base_agent import BaseAgent
from app.agents.constants import MOROCCO_ISO2, SOURCE_EUROSTAT

# ── Eurostat JSON-stat base URL ──
_ESTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

_INDICATOR_MAP = {
    "MIO_EXP_VAL": "export",
    "MIO_IMP_VAL": "import",
}

_SITC_LABEL_FR = {
    "TOTAL": "Total tous produits",
    "SITC0_1": "Produits alimentaires, boissons et tabac",
    "SITC2_4": "Matières premières",
    "SITC3": "Combustibles minéraux",
    "SITC5": "Produits chimiques",
    "SITC6_8": "Autres articles manufacturés (incl. textile)",
    "SITC7": "Machines et matériel de transport",
    "SITC9": "Autres produits",
}


class EurostatAgent(BaseAgent):
    source_name = SOURCE_EUROSTAT

    def fetch_data(self, **kwargs) -> int:
        total = 0
        try:
            total += self._fetch_eu_morocco_trade()
        except Exception as exc:
            self.logger.error(f"Eurostat EU-Morocco macro fetch failed: {exc}")
        self.logger.info(f"Eurostat fetch complete: {total} records upserted")
        return total

    # ── EU27 ↔ Morocco (ext_lt_maineu) ───────────────────
    def _fetch_eu_morocco_trade(self) -> int:
        url = f"{_ESTAT_BASE}/ext_lt_maineu"
        params = {
            "freq": "A",
            "partner": MOROCCO_ISO2,
            "geo": "EU27_2020",
            "sinceTimePeriod": str(date.today().year - 5),
        }
        resp = self.safe_request(url, params=params)
        self.increment_api_calls()
        return self._parse_jsonstat(resp.json(), "EU27", "Union Européenne")

    # ── JSON-stat decoder ────────────────────────────────
    def _parse_jsonstat(self, data: dict, reporter_code: str, reporter_name: str) -> int:
        values = data.get("value", {})
        if not values:
            self.logger.warning("Eurostat response contained no values")
            return 0

        dim_ids: list[str] = data["id"]
        dim_sizes: list[int] = data["size"]

        dim_code_by_pos: dict[str, dict[int, str]] = {}
        for dim_name in dim_ids:
            idx = data["dimension"][dim_name].get("category", {}).get("index", {})
            dim_code_by_pos[dim_name] = {v: k for k, v in idx.items()}

        count = 0
        for flat_str, value in values.items():
            if value is None:
                continue
            flat_idx = int(flat_str)
            coords: dict[str, int] = {}
            remaining = flat_idx
            for i in range(len(dim_ids) - 1, -1, -1):
                coords[dim_ids[i]] = remaining % dim_sizes[i]
                remaining //= dim_sizes[i]

            indic = dim_code_by_pos.get("indic_et", {}).get(coords.get("indic_et", 0), "")
            flow = _INDICATOR_MAP.get(indic)
            if flow is None:
                continue

            sitc = dim_code_by_pos.get("sitc06", {}).get(coords.get("sitc06", 0), "TOTAL")
            yr = dim_code_by_pos.get("time", {}).get(coords.get("time", 0), "")
            period_date = self._parse_period(yr)
            if period_date is None:
                continue

            value_eur = float(value) * 1_000_000  # MIO EUR → EUR

            filt = {
                "source": "eurostat",
                "reporter_code": reporter_code,
                "partner_code": MOROCCO_ISO2,
                "hs_code": sitc,
                "flow": flow,
                "period_date": datetime.combine(period_date, datetime.min.time()),
                "frequency": "A",
            }
            upd = {
                "reporter_name": reporter_name,
                "partner_name": "Maroc",
                "hs_description": _SITC_LABEL_FR.get(sitc, sitc),
                "value_eur": value_eur,
                "updated_at": datetime.now(timezone.utc),
            }
            self.db.trade_data.update_one(
                filt, {"$set": upd, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}}, upsert=True
            )
            count += 1
        return count

    @staticmethod
    def _parse_period(period_str: str) -> date | None:
        try:
            if "M" in period_str:
                parts = period_str.split("M")
                return date(int(parts[0]), int(parts[1]), 1)
            elif "Q" in period_str:
                parts = period_str.split("Q")
                return date(int(parts[0]), (int(parts[1]) - 1) * 3 + 1, 1)
            else:
                return date(int(period_str), 1, 1)
        except (ValueError, IndexError):
            return None
