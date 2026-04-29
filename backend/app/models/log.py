from datetime import datetime, date
from sqlalchemy import Text, Integer, Date, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HealthCheck(Base):
    __tablename__ = "health_check"

    id: Mapped[int] = mapped_column(primary_key=True)
    pc_name: Mapped[str] = mapped_column(Text, index=True)
    health_result: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    pc_name: Mapped[str] = mapped_column(Text, index=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    usage_date: Mapped[date] = mapped_column(Date, index=True, server_default=func.current_date())


class LastActive(Base):
    __tablename__ = "last_active"

    pc_name: Mapped[str] = mapped_column(Text, primary_key=True)
    last_active_at: Mapped[datetime] = mapped_column(server_default=func.now())


class TimesheetAutoLog(Base):
    __tablename__ = "timesheet_auto_logs"
    __table_args__ = (UniqueConstraint("username", "logged_date", name="uq_auto_logs_username_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    hostname: Mapped[str] = mapped_column(Text, index=True)
    username: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    ip: Mapped[str | None] = mapped_column(Text, nullable=True)
    check_in: Mapped[str | None] = mapped_column(Text, nullable=True)
    check_out: Mapped[str | None] = mapped_column(Text, nullable=True)
    onscreen_time: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_date: Mapped[str] = mapped_column(Text, index=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(server_default=func.now())


class TimesheetManualLog(Base):
    __tablename__ = "timesheet_manual_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(Text, index=True)
    check_in: Mapped[str] = mapped_column(Text)
    check_out: Mapped[str] = mapped_column(Text)
    logged_date: Mapped[str] = mapped_column(Text, index=True)
    status: Mapped[str] = mapped_column(Text)
    office_hour_work: Mapped[str | None] = mapped_column(Text, nullable=True)
    ot_work: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
