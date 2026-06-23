from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from indusense.db.base import Base


class Maintenance(Base):
    """Référentiel maintenances — miroir du schéma machine.sql."""

    __tablename__ = "maintenance"

    maintenance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    machine_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    maintenance_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    maintenance_type: Mapped[str] = mapped_column(String(16), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    component: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    related_incident_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    duration_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
