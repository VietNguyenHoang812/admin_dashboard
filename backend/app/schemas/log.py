from datetime import datetime, date
from pydantic import BaseModel


# ── Netclaw Health Check ────────────────────────────────────────────────────

class HealthCheckCreate(BaseModel):
    pc_name: str
    health_result: str


class HealthCheckRead(BaseModel):
    id: int
    pc_name: str
    health_result: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Token Usage ─────────────────────────────────────────────────────────────

class TokenUsageCreate(BaseModel):
    pc_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class TokenUsageRead(BaseModel):
    id: int
    pc_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    usage_date: date

    model_config = {"from_attributes": True}


# ── Last Active ─────────────────────────────────────────────────────────────

class LastActiveCreate(BaseModel):
    pc_name: str


class LastActiveRead(BaseModel):
    pc_name: str
    last_active_at: datetime

    model_config = {"from_attributes": True}


# ── Netclaw Stats (dashboard) ───────────────────────────────────────────────

class NetclawStats(BaseModel):
    total: int
    running: int
    degraded: int
    stopped: int
    by_day: list[dict]


# ── Timesheet Auto ──────────────────────────────────────────────────────────

class TimesheetEvent(BaseModel):
    type: str       # "startup" | "lock" | "unlock"
    timestamp: str  # ISO 8601 with TZ offset


class TimesheetAutoCreate(BaseModel):
    date: str
    hostname: str
    username: str
    platform: str | None = None
    events: list[TimesheetEvent]


class TimesheetAutoRead(BaseModel):
    id: int
    hostname: str
    username: str | None
    ip: str | None
    check_in: str | None
    check_out: str | None
    logged_date: str
    status: str | None
    received_at: datetime

    model_config = {"from_attributes": True}


# ── Timesheet Manual ────────────────────────────────────────────────────────

class TimesheetManualCreate(BaseModel):
    username: str
    check_in: str
    check_out: str
    logged_date: str
    status: str
    work_content: str | None = None


class TimesheetManualRead(BaseModel):
    id: int
    username: str
    check_in: str
    check_out: str
    logged_date: str
    status: str
    work_content: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Merged Timesheet ────────────────────────────────────────────────────────

class MergedTimesheetRead(BaseModel):
    id: int | None
    machine_id: str | None
    ip: str | None
    username: str | None
    usercode: str | None
    name: str | None
    department: str | None
    hostname: str | None
    auto_check_in: str | None
    auto_check_out: str | None
    manual_check_in: str | None
    manual_check_out: str | None
    work_content: str | None
    logged_date: str
    received_at: datetime
