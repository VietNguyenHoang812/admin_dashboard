from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pc import PC
from app.schemas.pc import PCCreate


async def upsert_pc(db: AsyncSession, data: PCCreate) -> PC:
    result = await db.execute(select(PC).where(PC.hostname == data.hostname))
    pc = result.scalar_one_or_none()

    if pc is None:
        pc = PC(**data.model_dump())
        db.add(pc)
    else:
        pc.ip_address = data.ip_address
        if data.os:
            pc.os = data.os

    pc.last_seen = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(pc)
    return pc
