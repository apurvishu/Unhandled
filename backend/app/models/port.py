"""Port model with PostGIS geometry."""

from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Port(Base):
    __tablename__ = "ports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    max_draft: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_loa: Mapped[float | None] = mapped_column(Float, nullable=True)
    cargo_capacity: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometry = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    berths = relationship("Berth", back_populates="port", cascade="all, delete-orphan")
    congestion_data = relationship("CongestionData", back_populates="port")
    destination_cargo = relationship(
        "CargoRequirement", back_populates="destination_port", foreign_keys="CargoRequirement.destination_port_id"
    )

    def __repr__(self) -> str:
        return f"<Port(id={self.id}, name='{self.name}', country='{self.country}')>"
