from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from indusense.db.base import Base


class BronzeIncident(Base):
    """Incidents nettoyés : dates UTC, FK machine validée, confidence_score inclus."""

    __tablename__ = "bronze_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    machine_id: Mapped[str] = mapped_column(
        String(16), ForeignKey("bronze_machine.machine_code"), nullable=False, index=True
    )
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    operator_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    operator_badge: Mapped[str | None] = mapped_column(String(50), nullable=True)
    severity: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    shift: Mapped[str | None] = mapped_column(String(20), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    type_surchauffe: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    type_baisse_pression: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    type_vibration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    type_bruit_mecanique: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    type_surconsommation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    type_blocage_mecanique: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    type_alarme_capteur: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    type_arret_urgence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    type_defaut_qualite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    bronze_data_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
