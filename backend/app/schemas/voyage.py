"""Voyage and port call schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.voyage import VoyageStatus
from app.models.port_call import PortCallStatus


class VoyageCreate(BaseModel):
    """Schema for creating a voyage."""
    vessel_id: int
    cargo_requirement_id: int | None = None
    origin_port_id: int
    destination_port_id: int
    departure_time: datetime | None = None
    estimated_arrival: datetime | None = None
    estimated_cost: float | None = Field(None, ge=0)


class VoyageUpdate(BaseModel):
    """Schema for updating a voyage."""
    departure_time: datetime | None = None
    estimated_arrival: datetime | None = None
    actual_arrival: datetime | None = None
    status: VoyageStatus | None = None
    estimated_cost: float | None = Field(None, ge=0)
    actual_cost: float | None = Field(None, ge=0)


class VoyageResponse(BaseModel):
    """Schema for voyage in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    vessel_id: int
    cargo_requirement_id: int | None = None
    origin_port_id: int
    destination_port_id: int
    departure_time: datetime | None = None
    estimated_arrival: datetime | None = None
    actual_arrival: datetime | None = None
    status: VoyageStatus
    estimated_cost: float | None = None
    actual_cost: float | None = None
    created_at: datetime


class PortCallCreate(BaseModel):
    """Schema for creating a port call."""
    voyage_id: int
    port_id: int
    berth_id: int | None = None
    eta: datetime | None = None
    etd: datetime | None = None


class PortCallUpdate(BaseModel):
    """Schema for updating a port call."""
    berth_id: int | None = None
    ata: datetime | None = None
    atd: datetime | None = None
    waiting_time: float | None = Field(None, ge=0)
    turnaround_time: float | None = Field(None, ge=0)
    status: PortCallStatus | None = None


class PortCallResponse(BaseModel):
    """Schema for port call in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    voyage_id: int
    port_id: int
    berth_id: int | None = None
    eta: datetime | None = None
    ata: datetime | None = None
    etd: datetime | None = None
    atd: datetime | None = None
    waiting_time: float | None = None
    turnaround_time: float | None = None
    status: PortCallStatus
