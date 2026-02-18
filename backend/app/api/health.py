from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db

router = APIRouter()


@router.get("")
async def health_check(db: AsyncIOMotorDatabase = Depends(get_db)):
    await db.command("ping")
    return {"status": "healthy", "db": "ok"}
