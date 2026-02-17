# MongoDB documents don't need ORM base classes.
# This module provides helper utilities for document creation.

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def timestamp_fields() -> dict:
    """Return a dict with created_at and updated_at set to now."""
    now = utcnow()
    return {"created_at": now, "updated_at": now}
