"""Voyage model with PostGIS route geometry."""

import enum
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VoyageStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DELAYED = "DELAYED"


class Voyage(Base):
    __tablename__ = "voyages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vessel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cargo_requirement_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cargo_requirements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    origin_port_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ports.id", ondelete="CASCADE"), nullable=False
    )
    destination_port_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ports.id", ondelete="CASCADE"), nullable=False
    )
    departure_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_arrival: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[VoyageStatus] = mapped_column(
        Enum(VoyageStatus), default=VoyageStatus.PLANNED, nullable=False
    )
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    route_geometry = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    vessel = relationship("Vessel", back_populates="voyages")
    cargo_requirement = relationship("CargoRequirement", back_populates="voyages")
    origin_port = relationship("Port", foreign_keys=[origin_port_id])
    destination_port = relationship("Port", foreign_keys=[destination_port_id])
    port_calls = relationship("PortCall", back_populates="voyage", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Voyage(id={self.id}, vessel_id={self.vessel_id}, status={self.status.value})>"
