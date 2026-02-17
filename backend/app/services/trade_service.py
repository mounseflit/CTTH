from datetime import date, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_trade_data(
    db: AsyncIOMotorDatabase,
    hs_codes: list[str] | None = None,
    partners: list[str] | None = None,
    flow: str | None = None,
    source: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    frequency: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[dict], int]:
    """Get paginated trade data with filters."""
    filter_dict: dict = {}

    if hs_codes:
        # Match HS codes by prefix (like SQL LIKE 'code%')
        conditions = [{"hs_code": {"$regex": f"^{code}"}} for code in hs_codes]
        if len(conditions) == 1:
            filter_dict.update(conditions[0])
        else:
            filter_dict["$or"] = conditions

    if partners:
        filter_dict["partner_code"] = {"$in": partners}

    if flow and flow != "all":
        filter_dict["flow"] = flow

    if source and source != "all":
        filter_dict["source"] = source

    if date_from:
        filter_dict.setdefault("period_date", {})["$gte"] = datetime.combine(date_from, datetime.min.time())

    if date_to:
        filter_dict.setdefault("period_date", {})["$lte"] = datetime.combine(date_to, datetime.min.time())

    if frequency:
        filter_dict["frequency"] = frequency

    total = await db.trade_data.count_documents(filter_dict)

    offset = (page - 1) * per_page
    cursor = (
        db.trade_data.find(filter_dict)
        .sort("period_date", -1)
        .skip(offset)
        .limit(per_page)
    )
    data = await cursor.to_list(length=per_page)

    return data, total


async def get_aggregated_data(
    db: AsyncIOMotorDatabase,
    group_by: str,
    flow: str | None = None,
    source: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[dict]:
    """Get aggregated trade data for charts."""
    match_stage: dict = {}

    if flow and flow != "all":
        match_stage["flow"] = flow
    if source and source != "all":
        match_stage["source"] = source
    if date_from:
        match_stage.setdefault("period_date", {})["$gte"] = datetime.combine(date_from, datetime.min.time())
    if date_to:
        match_stage.setdefault("period_date", {})["$lte"] = datetime.combine(date_to, datetime.min.time())

    if group_by == "partner":
        group_field = "$partner_name"
    elif group_by == "hs_code":
        group_field = {"$substr": ["$hs_code", 0, 2]}
    elif group_by == "flow":
        group_field = "$flow"
    else:
        group_field = "$partner_name"

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline.extend([
        {
            "$group": {
                "_id": group_field,
                "value": {
                    "$sum": {
                        "$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]
                    }
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"value": -1}},
        {"$limit": 50},
        {
            "$project": {
                "_id": 0,
                "label": {"$ifNull": ["$_id", "N/A"]},
                "value": 1,
                "count": 1,
            }
        },
    ])

    cursor = db.trade_data.aggregate(pipeline)
    return await cursor.to_list(length=50)


async def get_top_partners(
    db: AsyncIOMotorDatabase,
    flow: str | None = None,
    year: int | None = None,
    limit: int = 10,
) -> list[dict]:
    """Get top trading partners by value."""
    match_stage: dict = {"partner_code": {"$ne": "0"}}

    if flow and flow != "all":
        match_stage["flow"] = flow
    if year:
        match_stage["period_date"] = {
            "$gte": datetime(year, 1, 1),
            "$lte": datetime(year, 12, 31),
        }

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$partner_name",
                "value": {
                    "$sum": {
                        "$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]
                    }
                },
            }
        },
        {"$sort": {"value": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "label": "$_id", "value": 1}},
    ]

    cursor = db.trade_data.aggregate(pipeline)
    return await cursor.to_list(length=limit)


async def get_hs_breakdown(
    db: AsyncIOMotorDatabase,
    flow: str | None = None,
    year: int | None = None,
) -> list[dict]:
    """Get trade value breakdown by HS chapter."""
    match_stage: dict = {}

    if flow and flow != "all":
        match_stage["flow"] = flow
    if year:
        match_stage["period_date"] = {
            "$gte": datetime(year, 1, 1),
            "$lte": datetime(year, 12, 31),
        }

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline.extend([
        {
            "$group": {
                "_id": {"$substr": ["$hs_code", 0, 2]},
                "value": {
                    "$sum": {
                        "$ifNull": ["$value_usd", {"$ifNull": ["$value_eur", 0]}]
                    }
                },
            }
        },
        {"$sort": {"value": -1}},
        {"$project": {"_id": 0, "chapter": "$_id", "value": 1}},
    ])

    cursor = db.trade_data.aggregate(pipeline)
    return await cursor.to_list(length=100)
