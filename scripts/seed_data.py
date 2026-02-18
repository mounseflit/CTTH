"""
Seed script: creates default admin user and initializes data source status rows.

Usage:
    cd backend && python -m scripts.seed_data
    -- or --
    python scripts/seed_data.py
"""
import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure the backend package is importable
_here = os.path.dirname(os.path.abspath(__file__))
_backend = os.path.join(os.path.dirname(_here), "backend")
if _backend not in sys.path:
    sys.path.insert(0, _backend)

import bcrypt

from app.database import get_sync_db
from app.agents.constants import ALL_SOURCES


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed():
    db = get_sync_db()

    # ── Admin user ──────────────────────────────────────
    admin_email = "admin@ctth.ma"
    existing = db.users.find_one({"email": admin_email})

    if not existing:
        db.users.insert_one({
            "_id": str(uuid.uuid4()),
            "email": admin_email,
            "hashed_password": _hash_password("admin123"),
            "full_name": "Administrateur CTTH",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        })
        print("[OK] Admin user created: admin@ctth.ma / admin123")
    else:
        print("[SKIP] Admin user already exists")

    # ── Data source status rows ─────────────────────────
    for source_name in ALL_SOURCES:
        existing = db.data_source_status.find_one({"source_name": source_name})

        if not existing:
            db.data_source_status.insert_one({
                "_id": str(uuid.uuid4()),
                "source_name": source_name,
                "status": "active",
                "records_fetched_today": 0,
                "api_calls_today": 0,
                "last_successful_fetch": None,
                "last_error_message": None,
                "updated_at": datetime.now(timezone.utc),
            })
            print(f"[OK] Data source status created: {source_name}")
        else:
            print(f"[SKIP] Data source status exists: {source_name}")

    print("\nSeed complete!")


if __name__ == "__main__":
    seed()
