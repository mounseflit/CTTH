"""Market research document helpers for MongoDB."""
import uuid
from datetime import datetime, timezone


def new_segment_doc(
    axis: str,
    code: str,
    label_fr: str,
    label_en: str = "",
    parent_code: str | None = None,
    description_fr: str = "",
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "axis": axis,
        "code": code,
        "label_fr": label_fr,
        "label_en": label_en,
        "parent_code": parent_code,
        "description_fr": description_fr,
        "created_at": datetime.now(timezone.utc),
    }


def new_market_size_doc(
    segment_code: str,
    geography_code: str,
    year: int,
    value_usd: float,
    unit: str = "USD",
    source: str = "derived",
    flow: str = "total",
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "segment_code": segment_code,
        "geography_code": geography_code,
        "year": year,
        "value_usd": value_usd,
        "unit": unit,
        "flow": flow,
        "source": source,
        "created_at": datetime.now(timezone.utc),
    }


def new_company_doc(
    name: str,
    country: str = "MA",
    hq_city: str = "",
    description_fr: str = "",
    swot: dict | None = None,
    financials: dict | None = None,
    executives: list | None = None,
    website: str = "",
    sector: str = "textile",
    source: str = "ai_search",
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "name": name,
        "country": country,
        "hq_city": hq_city,
        "description_fr": description_fr,
        "swot": swot or {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
        "financials": financials or {},
        "executives": executives or [],
        "website": website,
        "sector": sector,
        "source": source,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def new_market_share_doc(
    company_name: str,
    segment_code: str,
    year: int,
    share_pct: float,
    value_usd: float = 0,
    source: str = "ai_search",
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "company_name": company_name,
        "segment_code": segment_code,
        "year": year,
        "share_pct": share_pct,
        "value_usd": value_usd,
        "source": source,
        "created_at": datetime.now(timezone.utc),
    }


def new_competitive_event_doc(
    event_type: str,
    company_name: str,
    title: str,
    description_fr: str = "",
    event_date: datetime | None = None,
    source_url: str = "",
    source_name: str = "",
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "event_type": event_type,  # m_and_a, partnership, expansion, regulation, investment
        "company_name": company_name,
        "title": title,
        "description_fr": description_fr,
        "event_date": event_date or datetime.now(timezone.utc),
        "source_url": source_url,
        "source_name": source_name,
        "created_at": datetime.now(timezone.utc),
    }


def new_insight_doc(
    category: str,
    title: str,
    narrative_fr: str,
    data_refs: list | None = None,
    droc_type: str | None = None,
    tags: list | None = None,
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "category": category,  # trend, risk, opportunity, challenge, driver
        "title": title,
        "narrative_fr": narrative_fr,
        "data_refs": data_refs or [],
        "droc_type": droc_type,  # driver, restraint, opportunity, challenge
        "tags": tags or [],
        "created_at": datetime.now(timezone.utc),
    }


def new_framework_result_doc(
    framework_type: str,
    content: dict,
    parameters: dict | None = None,
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "framework_type": framework_type,  # porter, pestel, tam_sam_som
        "content": content,
        "parameters": parameters or {},
        "created_at": datetime.now(timezone.utc),
    }
