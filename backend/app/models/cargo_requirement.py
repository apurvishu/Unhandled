"""Cargo requirement model for procurement officers."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.vessel import VesselType


class CargoStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class CargoRequirement(Base):
    __tablename__ = "cargo_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    procurement_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commodity: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_mt: Mapped[float] = mapped_column(Float, nullable=False)
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_port_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ports.id", ondelete="SET NULL"), nullable=True, index=True
    )
    required_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    preferred_vessel_type: Mapped[VesselType | None] = mapped_column(Enum(VesselType), nullable=True)
    status: Mapped[CargoStatus] = mapped_column(
        Enum(CargoStatus), default=CargoStatus.DRAFT, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    procurement_user = relationship("User", back_populates="cargo_requirements")
    destination_port = relationship("Port", back_populates="destination_cargo")
    charter_requests = relationship("CharterRequest", back_populates="cargo_requirement")
    voyages = relationship("Voyage", back_populates="cargo_requirement")

    def __repr__(self) -> str:
        return f"<CargoRequirement(id={self.id}, commodity='{self.commodity}', qty={self.quantity_mt})>"
