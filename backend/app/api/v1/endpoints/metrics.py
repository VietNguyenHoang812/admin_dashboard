from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.metric import MetricCreate, MetricRead
from app.services.metric_service import ingest_metric, get_recent_metrics

router = APIRouter()


@router.post("/ingest", response_model=MetricRead)
async def ingest(payload: MetricCreate, db: AsyncSession = Depends(get_db)):
    """Called by the background agent to push system metrics."""
    return await ingest_metric(db, payload)


@router.get("/{hostname}", response_model=list[MetricRead])
async def get_metrics(
    hostname: str,
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    return await get_recent_metrics(db, hostname, limit)
