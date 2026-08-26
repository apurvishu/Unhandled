"""Charter request, offer, and contract schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.charter_request import CharterRequestStatus
from app.models.charter_offer import OfferStatus
from app.models.charter_contract import ContractStatus, ContractType
from app.models.vessel import VesselType


# ===== Charter Requests =====

class CharterRequestCreate(BaseModel):
    """Schema for creating a charter request."""
    cargo_requirement_id: int
    vessel_type: VesselType | None = None
    minimum_dwt: float | None = Field(None, gt=0)
    maximum_draft: float | None = Field(None, gt=0)
    laycan_start: datetime | None = None
    laycan_end: datetime | None = None


class CharterRequestResponse(BaseModel):
    """Schema for charter request in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    cargo_requirement_id: int
    requested_by: int
    vessel_type: VesselType | None = None
    minimum_dwt: float | None = None
    maximum_draft: float | None = None
    laycan_start: datetime | None = None
    laycan_end: datetime | None = None
    status: CharterRequestStatus
    created_at: datetime


# ===== Charter Offers =====

class CharterOfferCreate(BaseModel):
    """Schema for creating a charter offer."""
    charter_request_id: int
    vessel_id: int
    freight_rate: float = Field(..., gt=0)
    total_cost: float | None = Field(None, gt=0)
    estimated_eta: datetime | None = None
    validity_until: datetime | None = None


class CharterOfferResponse(BaseModel):
    """Schema for charter offer in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    charter_request_id: int
    vessel_id: int
    freight_rate: float
    total_cost: float | None = None
    estimated_eta: datetime | None = None
    validity_until: datetime | None = None
    status: OfferStatus
    created_at: datetime


# ===== Offer Selection =====

class OfferSelectionRequest(BaseModel):
    """Schema for selecting a charter offer."""
    offer_id: int


# ===== Charter Contracts =====

class CharterContractCreate(BaseModel):
    """Schema for creating a charter contract."""
    charter_request_id: int
    selected_offer_id: int | None = None
    contract_type: ContractType
    agreed_rate: float = Field(..., gt=0)
    total_value: float | None = Field(None, gt=0)
    start_date: datetime | None = None
    end_date: datetime | None = None


class CharterContractResponse(BaseModel):
    """Schema for charter contract in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    charter_request_id: int
    selected_offer_id: int | None = None
    contract_type: ContractType
    agreed_rate: float
    total_value: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: ContractStatus
    created_at: datetime
