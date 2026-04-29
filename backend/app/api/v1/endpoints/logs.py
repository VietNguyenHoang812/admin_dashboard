from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.log import (
    TimesheetAutoCreate, TimesheetAutoRead,
    TimesheetManualCreate, TimesheetManualRead,
    MergedTimesheetRead,
)
from app.services.log_service import (
    create_timesheet_auto, get_timesheet_auto,
    create_timesheet_manual, get_timesheet_manual,
    get_merged_timesheets,
)

router = APIRouter()


# ── Timesheet Auto ──────────────────────────────────────────────────────────

@router.post(
    "/timesheet/auto",
    response_model=TimesheetAutoRead,
    tags=["logs"],
    summary="Ingest auto timesheet",
    description=(
        "PC agent pushes an automatic check-in / check-out record. "
        "`check_in` and `check_out` are time strings `HH:MM`. "
        "`logged_date` is a date string `YYYY-MM-DD`. "
        "`status` values: `present` | `late` | `absent`."
    ),
)
async def ingest_timesheet_auto(payload: TimesheetAutoCreate, db: AsyncSession = Depends(get_db)):
    return await create_timesheet_auto(db, payload)


@router.get(
    "/timesheet/auto",
    response_model=list[TimesheetAutoRead],
    tags=["logs"],
    summary="List auto timesheet records",
    description="Return recent automatic timesheet records ordered by most recent first.",
)
async def list_timesheet_auto(
    limit: int = Query(50, le=500, description="Maximum records to return (max 500)"),
    db: AsyncSession = Depends(get_db),
):
    return await get_timesheet_auto(db, limit)


# ── Timesheet Manual ────────────────────────────────────────────────────────

@router.post(
    "/timesheet/manual",
    response_model=TimesheetManualRead,
    tags=["logs"],
    summary="Ingest manual timesheet",
    description=(
        "User submits a manual timesheet entry with optional work content. "
        "`check_in` and `check_out` are time strings `HH:MM`. "
        "`logged_date` is a date string `YYYY-MM-DD`."
    ),
)
async def ingest_timesheet_manual(payload: TimesheetManualCreate, db: AsyncSession = Depends(get_db)):
    return await create_timesheet_manual(db, payload)


@router.get(
    "/timesheet/manual",
    response_model=list[TimesheetManualRead],
    tags=["logs"],
    summary="List manual timesheet entries",
    description="Return recent manual timesheet entries ordered by most recent first.",
)
async def list_timesheet_manual(
    limit: int = Query(50, le=500, description="Maximum records to return (max 500)"),
    db: AsyncSession = Depends(get_db),
):
    return await get_timesheet_manual(db, limit)


# ── Merged ──────────────────────────────────────────────────────────────────

@router.get(
    "/timesheet/merged",
    response_model=list[MergedTimesheetRead],
    tags=["logs"],
    summary="Merged timesheet view",
    description=(
        "Joins `timesheet_auto_logs` with `employees` and the most recent `timesheet_manual_logs` "
        "entry for the same `username` + `logged_date`. "
        "Provides a single unified row per machine per day with both auto and manual times."
    ),
)
async def list_timesheet_merged(
    limit: int = Query(1000, le=5000, description="Maximum records to return (max 5000)"),
    db: AsyncSession = Depends(get_db),
):
    return await get_merged_timesheets(db, limit)
