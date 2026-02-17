import re
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_news(
    db: AsyncIOMotorDatabase,
    category: str | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """Get news articles with optional text search."""
    filter_dict: dict = {}

    if category:
        filter_dict["category"] = category

    if search:
        # Use $regex for text search on title and summary
        escaped = re.escape(search)
        filter_dict["$or"] = [
            {"title": {"$regex": escaped, "$options": "i"}},
            {"summary": {"$regex": escaped, "$options": "i"}},
        ]

    if date_from:
        filter_dict.setdefault("published_at", {})["$gte"] = date_from

    if date_to:
        filter_dict.setdefault("published_at", {})["$lte"] = date_to

    total = await db.news_articles.count_documents(filter_dict)

    offset = (page - 1) * per_page
    cursor = (
        db.news_articles.find(filter_dict)
        .sort("published_at", -1)
        .skip(offset)
        .limit(per_page)
    )
    data = await cursor.to_list(length=per_page)

    return data, total
