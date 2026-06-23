import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from indusense.db.base import Base


class BronzeInvalidReason(str, enum.Enum):
    duplicate = "duplicate"
    missing_temperature = "missing_temperature"
    missing_pressure = "missing_pressure"
    missing_rotation_mean_rpm = "missing_rotation_mean_rpm"
    missing_voltage_mean_v = "missing_voltage_mean_v"
    missing_pieces_produced = "missing_pieces_produced"


class BronzeTelemetry(Base):
    """Telemetry nettoyée : dates UTC, FK machine validée."""

    __tablename__ = "bronze_telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    machine_id: Mapped[str] = mapped_column(
        String(16), ForeignKey("bronze_machine.machine_code"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_bar: Mapped[float | None] = mapped_column(Float, nullable=True)
    rotation_mean_rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    voltage_mean_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    pieces_produced: Mapped[float | None] = mapped_column(Float, nullable=True)

    bronze_data_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    bronze_data_comment: Mapped[str | None] = mapped_column(String(64), nullable=True)
