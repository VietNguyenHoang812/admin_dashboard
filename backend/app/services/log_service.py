from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import HealthcheckLog, TimesheetLog, TimesheetManualLog
from app.schemas.log import (
    HealthcheckLogCreate, TimesheetLogCreate, TimesheetManualLogCreate,
    MergedTimesheetRead, HealthcheckStats,
)


async def create_healthcheck_log(db: AsyncSession, data: HealthcheckLogCreate) -> HealthcheckLog:
    hc = data.netmind_healthcheck
    log = HealthcheckLog(
        machine_id=data.machine_id,
        ip=data.IP,
        timestamp=data.timestamp,
        version=hc.version if hc else None,
        status=hc.status if hc else None,
        active_services=hc.active_services if hc else None,
        last_ping=hc.last_ping if hc else None,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def create_timesheet_log(db: AsyncSession, data: TimesheetLogCreate) -> TimesheetLog:
    ts = data.timesheet_log
    log = TimesheetLog(
        machine_id=data.machine_id,
        ip=data.IP,
        timestamp=data.timestamp,
        check_in=ts.check_in if ts else None,
        check_out=ts.check_out if ts else None,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def create_timesheet_manual_log(db: AsyncSession, data: TimesheetManualLogCreate) -> TimesheetManualLog:
    ts = data.timesheet_log
    log = TimesheetManualLog(
        username=data.username,
        timestamp=data.timestamp,
        check_in=ts.check_in if ts else None,
        check_out=ts.check_out if ts else None,
        work_content=ts.work_content if ts else None,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def get_healthcheck_logs(db: AsyncSession, limit: int = 50) -> list[HealthcheckLog]:
    result = await db.execute(
        select(HealthcheckLog).order_by(HealthcheckLog.received_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_timesheet_logs(db: AsyncSession, limit: int = 50) -> list[TimesheetLog]:
    result = await db.execute(
        select(TimesheetLog).order_by(TimesheetLog.received_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_timesheet_manual_logs(db: AsyncSession, limit: int = 50) -> list[TimesheetManualLog]:
    result = await db.execute(
        select(TimesheetManualLog).order_by(TimesheetManualLog.received_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_merged_timesheets(db: AsyncSession, limit: int = 100) -> list[MergedTimesheetRead]:
    """
    Join timesheet_logs → employees (on ip) → timesheet_manual_logs (on username, same day).
    Uses a LATERAL subquery to pick the most recent manual log per machine per day.
    """
    sql = text("""
        SELECT
            tl.id,
            tl.machine_id,
            tl.ip,
            e.username,
            e.usercode,
            e.name,
            e.department,
            tl.check_in        AS ts_check_in,
            tl.check_out       AS ts_check_out,
            tm.check_in        AS manual_check_in,
            tm.check_out       AS manual_check_out,
            tm.work_content,
            tl.received_at
        FROM timesheet_logs tl
        LEFT JOIN employees e ON tl.ip = e.ip
        LEFT JOIN LATERAL (
            SELECT check_in, check_out, work_content
            FROM timesheet_manual_logs
            WHERE username = e.username
              AND DATE(received_at AT TIME ZONE 'UTC') = DATE(tl.received_at AT TIME ZONE 'UTC')
            ORDER BY received_at DESC
            LIMIT 1
        ) tm ON true
        ORDER BY tl.received_at DESC
        LIMIT :limit
    """)
    result = await db.execute(sql, {"limit": limit})
    rows = result.mappings().all()
    return [MergedTimesheetRead(**dict(row)) for row in rows]


async def get_healthcheck_stats(db: AsyncSession) -> HealthcheckStats:
    sql = text("""
        SELECT
            COUNT(*)                                                        AS total,
            COUNT(*) FILTER (WHERE status = 'Running')                     AS running,
            COUNT(*) FILTER (WHERE status = 'Degraded')                    AS degraded,
            COUNT(*) FILTER (WHERE status = 'Stopped')                     AS stopped
        FROM healthcheck_logs
        WHERE received_at >= NOW() - INTERVAL '7 days'
    """)
    row = (await db.execute(sql)).mappings().one()

    day_sql = text("""
        SELECT
            TO_CHAR(received_at AT TIME ZONE 'UTC', 'Dy') AS day,
            COUNT(*)                                        AS count
        FROM healthcheck_logs
        WHERE received_at >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(received_at AT TIME ZONE 'UTC'), TO_CHAR(received_at AT TIME ZONE 'UTC', 'Dy')
        ORDER BY DATE(received_at AT TIME ZONE 'UTC')
    """)
    day_rows = (await db.execute(day_sql)).mappings().all()

    return HealthcheckStats(
        total=row["total"],
        running=row["running"],
        degraded=row["degraded"],
        stopped=row["stopped"],
        by_day=[{"day": r["day"], "count": r["count"]} for r in day_rows],
    )
