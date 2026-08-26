"""Charter offer model."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OfferStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"


class CharterOffer(Base):
    __tablename__ = "charter_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    charter_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("charter_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vessel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    freight_rate: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validity_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus), default=OfferStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    charter_request = relationship("CharterRequest", back_populates="offers")
    vessel = relationship("Vessel", back_populates="charter_offers")
    selected_in_contracts = relationship("CharterContract", back_populates="selected_offer")

    def __repr__(self) -> str:
        return f"<CharterOffer(id={self.id}, rate={self.freight_rate}, status={self.status.value})>"
