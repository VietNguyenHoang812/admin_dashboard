from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.log import (
    HealthCheckCreate, HealthCheckRead,
    TokenUsageCreate, TokenUsageRead,
    LastActiveCreate, LastActiveRead,
    NetclawStats,
)
from app.services.log_service import (
    create_health_check, get_health_checks,
    create_token_usage, get_token_usages,
    upsert_last_active, get_last_actives,
    get_netclaw_stats,
)

router = APIRouter()


# ── Health Check ────────────────────────────────────────────────────────────

@router.post(
    "/health-check",
    response_model=HealthCheckRead,
    status_code=201,
    summary="Create health check",
    description="PC agent pushes a health check result. `health_result` is a free-form string (e.g. `OK`, `WARNING`, `ERROR`).",
)
async def create_health_check_endpoint(payload: HealthCheckCreate, db: AsyncSession = Depends(get_db)):
    return await create_health_check(db, payload)


@router.get(
    "/health-check",
    response_model=list[HealthCheckRead],
    summary="List health checks",
    description="Return recent health check records ordered by most recent first.",
)
async def list_health_checks(
    limit: int = Query(50, le=500, description="Maximum records to return (max 500)"),
    db: AsyncSession = Depends(get_db),
):
    return await get_health_checks(db, limit)


# ── Token Usage ─────────────────────────────────────────────────────────────

@router.post(
    "/token-usage",
    response_model=TokenUsageRead,
    status_code=201,
    summary="Create token usage",
    description="PC agent reports token consumption for the current session.",
)
async def create_token_usage_endpoint(payload: TokenUsageCreate, db: AsyncSession = Depends(get_db)):
    return await create_token_usage(db, payload)


@router.get(
    "/token-usage",
    response_model=list[TokenUsageRead],
    summary="List token usage",
    description="Return recent token usage records ordered by date descending.",
)
async def list_token_usage(
    limit: int = Query(50, le=500, description="Maximum records to return (max 500)"),
    db: AsyncSession = Depends(get_db),
):
    return await get_token_usages(db, limit)


# ── Last Active ─────────────────────────────────────────────────────────────

@router.post(
    "/last-active",
    response_model=LastActiveRead,
    status_code=201,
    summary="Create / update last active",
    description=(
        "Upsert the last-seen timestamp for a PC. "
        "Creates a new record on first call; updates `last_active_at` on subsequent calls for the same `pc_name`."
    ),
)
async def upsert_last_active_endpoint(payload: LastActiveCreate, db: AsyncSession = Depends(get_db)):
    return await upsert_last_active(db, payload)


@router.get(
    "/last-active",
    response_model=list[LastActiveRead],
    summary="List last active",
    description="Return all machines with their last-seen timestamp, ordered by most recent first.",
)
async def list_last_active(db: AsyncSession = Depends(get_db)):
    return await get_last_actives(db)


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=NetclawStats,
    summary="Netclaw statistics",
    description=(
        "Aggregate stats: total machines, online (active within last 5 minutes), offline, "
        "and daily health-check counts for the last 7 days."
    ),
)
async def netclaw_stats(db: AsyncSession = Depends(get_db)):
    return await get_netclaw_stats(db)
