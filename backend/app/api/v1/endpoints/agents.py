from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.pc import PCCreate, PCRead
from app.services.pc_service import upsert_pc

router = APIRouter()


@router.post("/register", response_model=PCRead)
async def register_agent(payload: PCCreate, db: AsyncSession = Depends(get_db)):
    """Called by the background agent on each PC to register or update its record."""
    return await upsert_pc(db, payload)
