"""Charter contract model."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContractType(str, enum.Enum):
    VOYAGE_CHARTER = "VOYAGE_CHARTER"
    TIME_CHARTER = "TIME_CHARTER"
    BAREBOAT_CHARTER = "BAREBOAT_CHARTER"
    CONTRACT_OF_AFFREIGHTMENT = "CONTRACT_OF_AFFREIGHTMENT"


class ContractStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    DISPUTED = "DISPUTED"


class CharterContract(Base):
    __tablename__ = "charter_contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    charter_request_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("charter_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    selected_offer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("charter_offers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contract_type: Mapped[ContractType] = mapped_column(Enum(ContractType), nullable=False)
    agreed_rate: Mapped[float] = mapped_column(Float, nullable=False)
    total_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus), default=ContractStatus.DRAFT, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    charter_request = relationship("CharterRequest", back_populates="contracts")
    selected_offer = relationship("CharterOffer", back_populates="selected_in_contracts")

    def __repr__(self) -> str:
        return f"<CharterContract(id={self.id}, type={self.contract_type.value}, status={self.status.value})>"
