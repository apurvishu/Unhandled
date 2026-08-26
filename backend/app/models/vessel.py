"""Vessel model with PostGIS current_position."""

import enum
from datetime import datetime, timezone, date

from geoalchemy2 import Geometry
from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VesselType(str, enum.Enum):
    PANAMAX = "PANAMAX"
    SUPRAMAX = "SUPRAMAX"
    CAPESIZE = "CAPESIZE"
    OTHER = "OTHER"


class VesselStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    EN_ROUTE = "EN_ROUTE"
    AT_PORT = "AT_PORT"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    LAID_UP = "LAID_UP"
    CHARTERED = "CHARTERED"


class Vessel(Base):
    __tablename__ = "vessels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    imo_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ship_owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ship_owners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vessel_type: Mapped[VesselType] = mapped_column(Enum(VesselType), nullable=False)
    dwt: Mapped[float] = mapped_column(Float, nullable=False)
    loa: Mapped[float | None] = mapped_column(Float, nullable=True)
    beam: Mapped[float | None] = mapped_column(Float, nullable=True)
    draft: Mapped[float | None] = mapped_column(Float, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    availability_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[VesselStatus] = mapped_column(
        Enum(VesselStatus), default=VesselStatus.AVAILABLE, nullable=False
    )
    current_position = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    ship_owner = relationship("ShipOwner", back_populates="vessels")
    charter_offers = relationship("CharterOffer", back_populates="vessel")
    voyages = relationship("Voyage", back_populates="vessel")
    ais_positions = relationship("AISPosition", back_populates="vessel", order_by="AISPosition.timestamp.desc()")

    def __repr__(self) -> str:
        return f"<Vessel(id={self.id}, name='{self.name}', imo='{self.imo_number}')>"
