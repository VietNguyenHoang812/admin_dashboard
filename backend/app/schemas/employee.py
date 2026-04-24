from pydantic import BaseModel
from datetime import datetime


class EmployeeCreate(BaseModel):
    username: str
    name: str
    usercode: str
    department: str | None = None
    ip: str | None = None
    hostname: str | None = None


class EmployeeUpdate(BaseModel):
    name: str | None = None
    usercode: str | None = None
    department: str | None = None
    ip: str | None = None
    hostname: str | None = None


class EmployeeRead(BaseModel):
    username: str
    name: str
    usercode: str
    department: str | None
    ip: str | None
    hostname: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
