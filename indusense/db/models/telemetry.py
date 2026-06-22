from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from indusense.db.base import Base


class Telemetry(Base):
    """Relevé de capteur pour une machine à un instant donné."""

    __tablename__ = "raw_telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    machine_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    pressure_bar: Mapped[float | None] = mapped_column(Float, nullable=True)
    rotation_mean_rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    voltage_mean_v: Mapped[float | None] = mapped_column(Float, nullable=True)
    pieces_produced: Mapped[float | None] = mapped_column(Float, nullable=True)
