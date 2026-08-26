"""Berth model with PostGIS geometry."""

import enum
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BerthStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    RESERVED = "RESERVED"


class Berth(Base):
    __tablename__ = "berths"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    port_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    max_draft: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_loa: Mapped[float | None] = mapped_column(Float, nullable=True)
    cargo_handling_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[BerthStatus] = mapped_column(
        Enum(BerthStatus), default=BerthStatus.AVAILABLE, nullable=False
    )
    geometry = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    port = relationship("Port", back_populates="berths")
    port_calls = relationship("PortCall", back_populates="berth")

    def __repr__(self) -> str:
        return f"<Berth(id={self.id}, name='{self.name}', port_id={self.port_id})>"
