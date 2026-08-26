"""Port call model for tracking vessel stops at ports."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PortCallStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    WAITING = "WAITING"
    AT_BERTH = "AT_BERTH"
    DEPARTED = "DEPARTED"
    CANCELLED = "CANCELLED"


class PortCall(Base):
    __tablename__ = "port_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voyage_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("voyages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    port_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    berth_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("berths.id", ondelete="SET NULL"), nullable=True
    )
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ata: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    etd: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    atd: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    waiting_time: Mapped[float | None] = mapped_column(Float, nullable=True)  # hours
    turnaround_time: Mapped[float | None] = mapped_column(Float, nullable=True)  # hours
    status: Mapped[PortCallStatus] = mapped_column(
        Enum(PortCallStatus), default=PortCallStatus.SCHEDULED, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    voyage = relationship("Voyage", back_populates="port_calls")
    port = relationship("Port")
    berth = relationship("Berth", back_populates="port_calls")

    def __repr__(self) -> str:
        return f"<PortCall(id={self.id}, voyage_id={self.voyage_id}, port_id={self.port_id})>"
