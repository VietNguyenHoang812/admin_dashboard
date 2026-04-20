from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric import Metric
from app.models.pc import PC
from app.schemas.metric import MetricCreate
from app.services.pc_service import upsert_pc
from app.schemas.pc import PCCreate


async def ingest_metric(db: AsyncSession, data: MetricCreate) -> Metric:
    pc = await upsert_pc(db, PCCreate(hostname=data.hostname, ip_address="unknown"))

    metric = Metric(
        pc_id=pc.id,
        cpu_percent=data.cpu_percent,
        memory_percent=data.memory_percent,
        disk_percent=data.disk_percent,
    )
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric


async def get_recent_metrics(db: AsyncSession, hostname: str, limit: int = 100) -> list[Metric]:
    result = await db.execute(
        select(Metric)
        .join(PC, Metric.pc_id == PC.id)
        .where(PC.hostname == hostname)
        .order_by(Metric.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
