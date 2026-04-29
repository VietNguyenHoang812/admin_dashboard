from datetime import datetime, timedelta, timezone
from dateutil import parser as dtparse

from fastapi import HTTPException
from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import (
    HealthCheck, TokenUsage, LastActive,
    TimesheetAutoLog, TimesheetManualLog,
)
from app.schemas.log import (
    HealthCheckCreate, TokenUsageCreate, LastActiveCreate, NetclawStats,
    TimesheetAutoCreate, TimesheetManualCreate, MergedTimesheetRead,
)


# ── Netclaw Health Check ────────────────────────────────────────────────────

async def create_health_check(db: AsyncSession, data: HealthCheckCreate) -> HealthCheck:
    row = HealthCheck(**data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_health_checks(db: AsyncSession, limit: int = 50) -> list[HealthCheck]:
    result = await db.execute(
        select(HealthCheck).order_by(HealthCheck.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ── Token Usage ─────────────────────────────────────────────────────────────

async def create_token_usage(db: AsyncSession, data: TokenUsageCreate) -> TokenUsage:
    row = TokenUsage(**data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_token_usages(db: AsyncSession, limit: int = 50) -> list[TokenUsage]:
    result = await db.execute(
        select(TokenUsage).order_by(TokenUsage.usage_date.desc(), TokenUsage.id.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ── Last Active ─────────────────────────────────────────────────────────────

async def upsert_last_active(db: AsyncSession, data: LastActiveCreate) -> LastActive:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stmt = (
        pg_insert(LastActive)
        .values(pc_name=data.pc_name, last_active_at=now)
        .on_conflict_do_update(
            index_elements=["pc_name"],
            set_={"last_active_at": now},
        )
    )
    await db.execute(stmt)
    await db.commit()
    result = await db.execute(select(LastActive).where(LastActive.pc_name == data.pc_name))
    return result.scalar_one()


async def get_last_actives(db: AsyncSession) -> list[LastActive]:
    result = await db.execute(
        select(LastActive).order_by(LastActive.last_active_at.desc())
    )
    return list(result.scalars().all())


# ── Netclaw Stats ───────────────────────────────────────────────────────────

async def get_netclaw_stats(db: AsyncSession) -> NetclawStats:
    five_min_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)

    total_r = await db.execute(select(text("COUNT(*)")).select_from(LastActive))
    total = total_r.scalar() or 0

    online_r = await db.execute(
        select(text("COUNT(*)")).select_from(LastActive)
        .where(LastActive.last_active_at >= five_min_ago)
    )
    running = online_r.scalar() or 0
    stopped = total - running

    day_sql = text("""
        SELECT
            TO_CHAR(created_at, 'Dy') AS day,
            COUNT(*)                  AS count
        FROM health_check
        WHERE created_at >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(created_at), TO_CHAR(created_at, 'Dy')
        ORDER BY DATE(created_at)
    """)
    day_rows = (await db.execute(day_sql)).mappings().all()

    return NetclawStats(
        total=total,
        running=running,
        degraded=0,
        stopped=stopped,
        by_day=[{"day": r["day"], "count": r["count"]} for r in day_rows],
    )


# ── Timesheet Auto ──────────────────────────────────────────────────────────

def _derive_checkin_checkout(events: list) -> tuple[str | None, str | None]:
    """
    check_in  = earliest of first startup or first lock event
    check_out = last lock event timestamp
    """
    startups = [dtparse.parse(e.timestamp) for e in events if e.type == "startup"]
    locks    = [dtparse.parse(e.timestamp) for e in events if e.type == "lock"]

    check_in: str | None = None
    if startups or locks:
        candidates = startups[:1] + locks[:1]
        earliest = min(candidates)
        check_in = earliest.strftime("%H:%M")

    check_out: str | None = None
    if locks:
        check_out = max(locks).strftime("%H:%M")

    return check_in, check_out


def _compute_onscreen_time(events: list) -> str | None:
    """Total duration screen was active (between startup/unlock → lock pairs)."""
    from datetime import timedelta
    total = timedelta()
    on_since = None

    for e in sorted(events, key=lambda x: dtparse.parse(x.timestamp)):
        ts = dtparse.parse(e.timestamp)
        if e.type in ("startup", "unlock"):
            if on_since is None:
                on_since = ts
        elif e.type == "lock" and on_since is not None:
            diff = ts - on_since
            if diff.total_seconds() > 0:
                total += diff
            on_since = None

    secs = int(total.total_seconds())
    if secs <= 0:
        return None
    return f"{secs // 3600}:{(secs % 3600) // 60:02d}"


async def create_timesheet_auto(db: AsyncSession, data: TimesheetAutoCreate) -> TimesheetAutoLog:
    check_in, check_out = _derive_checkin_checkout(data.events)
    onscreen_time = _compute_onscreen_time(data.events)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    stmt = (
        pg_insert(TimesheetAutoLog)
        .values(
            hostname=data.hostname,
            username=data.username,
            ip=data.ip,
            check_in=check_in,
            check_out=check_out,
            onscreen_time=onscreen_time,
            logged_date=data.logged_date,
            status=None,
            received_at=now,
        )
        .on_conflict_do_update(
            constraint="uq_auto_logs_username_date",
            set_={
                "hostname": data.hostname,
                "ip": data.ip,
                "check_in": check_in,
                "check_out": check_out,
                "onscreen_time": onscreen_time,
                "received_at": now,
            },
        )
    )
    await db.execute(stmt)
    await db.commit()
    result = await db.execute(
        select(TimesheetAutoLog)
        .where(TimesheetAutoLog.username == data.username)
        .where(TimesheetAutoLog.logged_date == data.logged_date)
    )
    return result.scalar_one()


async def get_timesheet_auto(db: AsyncSession, limit: int = 50) -> list[TimesheetAutoLog]:
    result = await db.execute(
        select(TimesheetAutoLog).order_by(TimesheetAutoLog.received_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ── Timesheet Manual ────────────────────────────────────────────────────────

async def create_timesheet_manual(db: AsyncSession, data: TimesheetManualCreate) -> TimesheetManualLog:
    existing_r = await db.execute(
        select(TimesheetManualLog)
        .where(TimesheetManualLog.username == data.username)
        .where(TimesheetManualLog.logged_date == data.logged_date)
    )
    existing = list(existing_r.scalars().all())

    if existing:
        if data.status == "absent":
            await db.execute(
                delete(TimesheetManualLog)
                .where(TimesheetManualLog.username == data.username)
                .where(TimesheetManualLog.logged_date == data.logged_date)
            )
        else:
            existing_statuses = {r.status for r in existing}
            if len(existing) >= 2:
                raise HTTPException(status_code=409, detail="Đã có 2 bản ghi cho ngày này, không thể thêm.")
            if data.status in existing_statuses:
                raise HTTPException(status_code=409, detail=f"Đã có bản ghi với trạng thái '{data.status}' cho ngày này.")
            allowed_pair = {"present", "upcode"}
            if not ({data.status} | existing_statuses).issubset(allowed_pair):
                raise HTTPException(status_code=409, detail="Chỉ cho phép kết hợp 'present' và 'upcode' trong cùng một ngày.")

    row = TimesheetManualLog(**data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_timesheet_manual(db: AsyncSession, limit: int = 50) -> list[TimesheetManualLog]:
    result = await db.execute(
        select(TimesheetManualLog).order_by(TimesheetManualLog.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ── Merged Timesheet ────────────────────────────────────────────────────────

async def get_merged_timesheets(db: AsyncSession, limit: int = 100) -> list[MergedTimesheetRead]:
    sql = text("""
        -- Auto logs: one row per (username, logged_date), earliest check_in + latest check_out
        WITH auto_agg AS (
            SELECT
                username,
                logged_date,
                MIN(check_in)      AS auto_check_in,
                MAX(check_out)     AS auto_check_out,
                MAX(onscreen_time) AS onscreen_time,
                MAX(received_at)   AS received_at
            FROM timesheet_auto_logs
            WHERE username IS NOT NULL
            GROUP BY username, logged_date
        )

        SELECT
            NULL::int          AS id,
            NULL               AS machine_id,
            e.ip,
            e.username,
            e.usercode,
            e.name,
            e.department,
            e.hostname,
            aa.auto_check_in,
            aa.auto_check_out,
            aa.onscreen_time,
            tm.check_in        AS manual_check_in,
            tm.check_out       AS manual_check_out,
            tm.office_hour_work,
            tm.ot_work AS "ot_work",
            tm.status,
            aa.logged_date,
            aa.received_at
        FROM auto_agg aa
        JOIN employees e ON aa.username = e.username
        LEFT JOIN LATERAL (
            SELECT DISTINCT ON (status) check_in, check_out, office_hour_work, ot_work, status
            FROM timesheet_manual_logs
            WHERE username = aa.username
              AND logged_date = aa.logged_date
            ORDER BY status, created_at DESC
        ) tm ON true

        UNION ALL

        -- Manual-only: employees who have no auto log that day (one row per user+date, latest entry)
        SELECT
            NULL::int          AS id,
            NULL               AS machine_id,
            e2.ip,
            e2.username,
            e2.usercode,
            e2.name,
            e2.department,
            e2.hostname,
            NULL               AS auto_check_in,
            NULL               AS auto_check_out,
            NULL               AS onscreen_time,
            mo.check_in        AS manual_check_in,
            mo.check_out       AS manual_check_out,
            mo.office_hour_work,
            mo.ot_work AS "ot_work",
            mo.status,
            mo.logged_date,
            mo.created_at      AS received_at
        FROM (
            SELECT DISTINCT ON (username, logged_date, status) *
            FROM timesheet_manual_logs
            ORDER BY username, logged_date, status, created_at DESC
        ) mo
        JOIN employees e2 ON mo.username = e2.username
        WHERE NOT EXISTS (
            SELECT 1 FROM timesheet_auto_logs ta2
            WHERE ta2.username = mo.username
              AND ta2.logged_date = mo.logged_date
        )

        ORDER BY received_at DESC
        LIMIT :limit
    """)
    result = await db.execute(sql, {"limit": limit})
    rows = result.mappings().all()
    return [MergedTimesheetRead(**dict(row)) for row in rows]
