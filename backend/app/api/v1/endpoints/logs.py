from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.log import (
    HealthcheckLogCreate, HealthcheckLogRead,
    TimesheetLogCreate, TimesheetLogRead,
    TimesheetManualLogCreate, TimesheetManualLogRead,
    MergedTimesheetRead, HealthcheckStats,
)
from app.services.log_service import (
    create_healthcheck_log, get_healthcheck_logs,
    create_timesheet_log, get_timesheet_logs,
    create_timesheet_manual_log, get_timesheet_manual_logs,
    get_merged_timesheets, get_healthcheck_stats,
)

router = APIRouter()


@router.post("/healthcheck", response_model=HealthcheckLogRead)
async def ingest_healthcheck(payload: HealthcheckLogCreate, db: AsyncSession = Depends(get_db)):
    return await create_healthcheck_log(db, payload)


@router.get("/healthcheck", response_model=list[HealthcheckLogRead])
async def list_healthcheck(limit: int = Query(50, le=500), db: AsyncSession = Depends(get_db)):
    return await get_healthcheck_logs(db, limit)


@router.get("/healthcheck/stats", response_model=HealthcheckStats)
async def healthcheck_stats(db: AsyncSession = Depends(get_db)):
    return await get_healthcheck_stats(db)


@router.post("/timesheet", response_model=TimesheetLogRead)
async def ingest_timesheet(payload: TimesheetLogCreate, db: AsyncSession = Depends(get_db)):
    return await create_timesheet_log(db, payload)


@router.get("/timesheet", response_model=list[TimesheetLogRead])
async def list_timesheet(limit: int = Query(50, le=500), db: AsyncSession = Depends(get_db)):
    return await get_timesheet_logs(db, limit)


@router.post("/timesheet/manual", response_model=TimesheetManualLogRead)
async def ingest_timesheet_manual(payload: TimesheetManualLogCreate, db: AsyncSession = Depends(get_db)):
    return await create_timesheet_manual_log(db, payload)


@router.get("/timesheet/manual", response_model=list[TimesheetManualLogRead])
async def list_timesheet_manual(limit: int = Query(50, le=500), db: AsyncSession = Depends(get_db)):
    return await get_timesheet_manual_logs(db, limit)


@router.get("/timesheet/merged", response_model=list[MergedTimesheetRead])
async def list_timesheet_merged(limit: int = Query(100, le=500), db: AsyncSession = Depends(get_db)):
    return await get_merged_timesheets(db, limit)
