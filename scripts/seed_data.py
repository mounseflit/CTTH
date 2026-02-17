"""
Seed script: creates default admin user and initializes data source status rows.

Usage:
    docker compose exec backend python scripts/seed_data.py
"""
import sys
import uuid

sys.path.insert(0, "/app")

from passlib.context import CryptContext
from sqlalchemy import text

from app.database import sync_engine, SyncSessionLocal
from app.models import Base
from app.agents.constants import ALL_SOURCES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    # Create tables if they don't exist (fallback if Alembic hasn't run)
    Base.metadata.create_all(sync_engine)

    with SyncSessionLocal() as db:
        # Create admin user
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": "admin@ctth.ma"},
        ).fetchone()

        if not existing:
            db.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, full_name, role, is_active)
                    VALUES (:id, :email, :password, :name, :role, true)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "email": "admin@ctth.ma",
                    "password": pwd_context.hash("admin123"),
                    "name": "Administrateur CTTH",
                    "role": "admin",
                },
            )
            print("[OK] Admin user created: admin@ctth.ma / admin123")
        else:
            print("[SKIP] Admin user already exists")

        # Create data source status rows
        for source_name in ALL_SOURCES:
            existing = db.execute(
                text(
                    "SELECT id FROM data_source_status WHERE source_name = :name"
                ),
                {"name": source_name},
            ).fetchone()

            if not existing:
                db.execute(
                    text("""
                        INSERT INTO data_source_status (id, source_name, status, records_fetched_today, api_calls_today)
                        VALUES (:id, :name, 'active', 0, 0)
                    """),
                    {"id": str(uuid.uuid4()), "name": source_name},
                )
                print(f"[OK] Data source status created: {source_name}")
            else:
                print(f"[SKIP] Data source status exists: {source_name}")

        db.commit()

    print("\nSeed complete!")


if __name__ == "__main__":
    seed()
