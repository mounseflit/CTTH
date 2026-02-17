"""User document helpers for MongoDB."""
import uuid
from datetime import datetime, timezone


def new_user_doc(
    email: str,
    hashed_password: str,
    full_name: str | None = None,
    role: str = "analyst",
) -> dict:
    return {
        "_id": str(uuid.uuid4()),
        "email": email,
        "hashed_password": hashed_password,
        "full_name": full_name,
        "role": role,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
