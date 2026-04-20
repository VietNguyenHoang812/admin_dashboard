from datetime import datetime
from pydantic import BaseModel


class PCCreate(BaseModel):
    hostname: str
    ip_address: str
    os: str | None = None


class PCRead(BaseModel):
    id: int
    hostname: str
    ip_address: str
    os: str | None
    last_seen: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
