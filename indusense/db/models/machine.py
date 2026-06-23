from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from indusense.db.base import Base


class Machine(Base):
    """Référentiel machines — miroir du schéma machine.sql (utilisé pour la FK bronze)."""

    __tablename__ = "machine"

    machine_code: Mapped[str] = mapped_column(String(16), primary_key=True)
    run_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    commissioning_date: Mapped[date] = mapped_column(Date, nullable=False)
    max_daily_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    max_hourly_capacity_pieces: Mapped[int] = mapped_column(Integer, nullable=False)
    model: Mapped[str] = mapped_column(String(32), nullable=False)
    production_line: Mapped[str] = mapped_column(String(16), nullable=False)
    location: Mapped[str] = mapped_column(String(16), nullable=False)
    criticality: Mapped[str] = mapped_column(String(8), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
