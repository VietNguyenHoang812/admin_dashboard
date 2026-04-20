from datetime import datetime
from pydantic import BaseModel


class MetricCreate(BaseModel):
    hostname: str
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent: float | None = None


class MetricRead(BaseModel):
    id: int
    pc_id: int
    cpu_percent: float | None
    memory_percent: float | None
    disk_percent: float | None
    timestamp: datetime

    model_config = {"from_attributes": True}
