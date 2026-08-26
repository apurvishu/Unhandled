"""Charter request model."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.vessel import VesselType


class CharterRequestStatus(str, enum.Enum):
    OPEN = "OPEN"
    OFFERS_RECEIVED = "OFFERS_RECEIVED"
    UNDER_REVIEW = "UNDER_REVIEW"
    AWARDED = "AWARDED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class CharterRequest(Base):
    __tablename__ = "charter_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cargo_requirement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cargo_requirements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vessel_type: Mapped[VesselType | None] = mapped_column(Enum(VesselType), nullable=True)
    minimum_dwt: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_draft: Mapped[float | None] = mapped_column(Float, nullable=True)
    laycan_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    laycan_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[CharterRequestStatus] = mapped_column(
        Enum(CharterRequestStatus), default=CharterRequestStatus.OPEN, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    cargo_requirement = relationship("CargoRequirement", back_populates="charter_requests")
    requester = relationship("User", foreign_keys=[requested_by])
    offers = relationship("CharterOffer", back_populates="charter_request", cascade="all, delete-orphan")
    contracts = relationship("CharterContract", back_populates="charter_request")

    def __repr__(self) -> str:
        return f"<CharterRequest(id={self.id}, status={self.status.value})>"
