from pydantic import BaseModel
from datetime import datetime


class EmployeeCreate(BaseModel):
    name: str
    usercode: str
    username: str
    department: str | None = None
    ip: str | None = None


class EmployeeUpdate(BaseModel):
    name: str | None = None
    usercode: str | None = None
    username: str | None = None
    department: str | None = None
    ip: str | None = None


class EmployeeRead(BaseModel):
    id: int
    name: str
    usercode: str
    username: str
    department: str | None
    ip: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
