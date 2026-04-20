from sqlalchemy import String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.core.database import Base


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("usercode", name="uq_employee_usercode"),
        UniqueConstraint("username", name="uq_employee_username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    usercode: Mapped[str] = mapped_column(String(100), index=True)
    username: Mapped[str] = mapped_column(String(100), index=True)
    department: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
