"""Cargo requirement schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.cargo_requirement import CargoStatus
from app.models.vessel import VesselType


class CargoCreate(BaseModel):
    """Schema for creating a cargo requirement."""
    commodity: str = Field(..., min_length=1, max_length=255)
    quantity_mt: float = Field(..., gt=0, description="Quantity in metric tons")
    origin: str = Field(..., min_length=1, max_length=255)
    destination_port_id: int | None = None
    required_arrival: datetime | None = None
    preferred_vessel_type: VesselType | None = None


class CargoUpdate(BaseModel):
    """Schema for updating a cargo requirement."""
    commodity: str | None = Field(None, min_length=1, max_length=255)
    quantity_mt: float | None = Field(None, gt=0)
    origin: str | None = Field(None, min_length=1, max_length=255)
    destination_port_id: int | None = None
    required_arrival: datetime | None = None
    preferred_vessel_type: VesselType | None = None
    status: CargoStatus | None = None


class CargoResponse(BaseModel):
    """Schema for cargo requirement in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    procurement_user_id: int
    commodity: str
    quantity_mt: float
    origin: str
    destination_port_id: int | None = None
    required_arrival: datetime | None = None
    preferred_vessel_type: VesselType | None = None
    status: CargoStatus
    created_at: datetime
