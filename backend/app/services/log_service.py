from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
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

async def create_timesheet_auto(db: AsyncSession, data: TimesheetAutoCreate) -> TimesheetAutoLog:
    row = TimesheetAutoLog(**data.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_timesheet_auto(db: AsyncSession, limit: int = 50) -> list[TimesheetAutoLog]:
    result = await db.execute(
        select(TimesheetAutoLog).order_by(TimesheetAutoLog.received_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


# ── Timesheet Manual ────────────────────────────────────────────────────────

async def create_timesheet_manual(db: AsyncSession, data: TimesheetManualCreate) -> TimesheetManualLog:
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
        SELECT
            ta.id,
            ta.machine_id,
            ta.ip,
            e.username,
            e.usercode,
            e.name,
            e.department,
            e.hostname,
            ta.check_in        AS auto_check_in,
            ta.check_out       AS auto_check_out,
            tm.check_in        AS manual_check_in,
            tm.check_out       AS manual_check_out,
            tm.work_content,
            ta.logged_date,
            ta.received_at
        FROM timesheet_auto_logs ta
        LEFT JOIN employees e ON ta.ip = e.ip
        LEFT JOIN LATERAL (
            SELECT check_in, check_out, work_content
            FROM timesheet_manual_logs
            WHERE username = e.username
              AND logged_date = ta.logged_date
            ORDER BY created_at DESC
            LIMIT 1
        ) tm ON true

        UNION ALL

        SELECT
            NULL               AS id,
            NULL               AS machine_id,
            e2.ip,
            e2.username,
            e2.usercode,
            e2.name,
            e2.department,
            e2.hostname,
            NULL               AS auto_check_in,
            NULL               AS auto_check_out,
            mo.check_in        AS manual_check_in,
            mo.check_out       AS manual_check_out,
            mo.work_content,
            mo.logged_date,
            mo.created_at      AS received_at
        FROM timesheet_manual_logs mo
        JOIN employees e2 ON mo.username = e2.username
        WHERE NOT EXISTS (
            SELECT 1
            FROM timesheet_auto_logs ta2
            JOIN employees ex ON ta2.ip = ex.ip
            WHERE ex.username = mo.username
              AND ta2.logged_date = mo.logged_date
        )

        ORDER BY received_at DESC
        LIMIT :limit
    """)
    result = await db.execute(sql, {"limit": limit})
    rows = result.mappings().all()
    return [MergedTimesheetRead(**dict(row)) for row in rows]
