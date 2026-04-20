from datetime import datetime
from pydantic import BaseModel


class NetmindHealthcheck(BaseModel):
    version: str | None = None
    status: str | None = None
    active_services: int | None = None
    last_ping: datetime | None = None


class HealthcheckLogCreate(BaseModel):
    machine_id: str
    IP: str
    timestamp: datetime
    netmind_healthcheck: NetmindHealthcheck | None = None


class HealthcheckLogRead(BaseModel):
    id: int
    machine_id: str
    ip: str
    version: str | None
    status: str | None
    active_services: int | None
    last_ping: datetime | None
    timestamp: datetime
    received_at: datetime

    model_config = {"from_attributes": True}


class TimesheetEntry(BaseModel):
    check_in: datetime | None = None
    check_out: datetime | None = None


class TimesheetLogCreate(BaseModel):
    machine_id: str
    IP: str
    timestamp: datetime
    timesheet_log: TimesheetEntry | None = None


class TimesheetLogRead(BaseModel):
    id: int
    machine_id: str
    ip: str
    check_in: datetime | None
    check_out: datetime | None
    timestamp: datetime
    received_at: datetime

    model_config = {"from_attributes": True}


class TimesheetManualEntry(BaseModel):
    check_in: datetime | None = None
    check_out: datetime | None = None
    work_content: str | None = None


class TimesheetManualLogCreate(BaseModel):
    username: str
    timestamp: datetime
    timesheet_log: TimesheetManualEntry | None = None


class TimesheetManualLogRead(BaseModel):
    id: int
    username: str
    check_in: datetime | None
    check_out: datetime | None
    work_content: str | None
    timestamp: datetime
    received_at: datetime

    model_config = {"from_attributes": True}


class HealthcheckStats(BaseModel):
    total: int
    running: int
    degraded: int
    stopped: int
    by_day: list[dict]  # [{day, count}]


class MergedTimesheetRead(BaseModel):
    id: int
    machine_id: str
    ip: str
    username: str | None
    usercode: str | None
    name: str | None
    department: str | None
    ts_check_in: datetime | None
    ts_check_out: datetime | None
    manual_check_in: datetime | None
    manual_check_out: datetime | None
    work_content: str | None
    received_at: datetime
