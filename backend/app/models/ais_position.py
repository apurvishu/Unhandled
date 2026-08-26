"""AIS position model with PostGIS Point geometry and spatial index."""

from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AISPosition(Base):
    __tablename__ = "ais_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vessel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    course: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    navigation_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    vessel = relationship("Vessel", back_populates="ais_positions")

    def __repr__(self) -> str:
        return f"<AISPosition(id={self.id}, vessel_id={self.vessel_id}, lat={self.latitude}, lon={self.longitude})>"
