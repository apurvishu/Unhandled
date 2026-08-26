"""Port congestion data model."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CongestionLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CongestionData(Base):
    __tablename__ = "congestion_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    port_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    vessels_waiting: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vessels_at_berth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_waiting_time: Mapped[float | None] = mapped_column(Float, nullable=True)  # hours
    berth_utilization: Mapped[float | None] = mapped_column(Float, nullable=True)  # percentage
    congestion_level: Mapped[CongestionLevel | None] = mapped_column(Enum(CongestionLevel), nullable=True)
    predicted_waiting_time: Mapped[float | None] = mapped_column(Float, nullable=True)  # hours
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    port = relationship("Port", back_populates="congestion_data")

    def __repr__(self) -> str:
        return f"<CongestionData(id={self.id}, port_id={self.port_id}, level={self.congestion_level})>"
