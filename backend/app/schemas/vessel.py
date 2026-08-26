"""Vessel schemas with validation."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.vessel import VesselStatus, VesselType


class VesselCreate(BaseModel):
    """Schema for creating a vessel."""
    imo_number: str = Field(..., min_length=7, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    vessel_type: VesselType
    dwt: float = Field(..., gt=0, description="Deadweight tonnage")
    loa: float | None = Field(None, gt=0, description="Length overall in meters")
    beam: float | None = Field(None, gt=0, description="Beam width in meters")
    draft: float | None = Field(None, gt=0, description="Draft in meters")
    year_built: int | None = Field(None, ge=1900, le=2030)
    flag: str | None = Field(None, max_length=100)
    availability_date: date | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)


class VesselUpdate(BaseModel):
    """Schema for updating a vessel."""
    name: str | None = Field(None, min_length=1, max_length=255)
    vessel_type: VesselType | None = None
    dwt: float | None = Field(None, gt=0)
    loa: float | None = Field(None, gt=0)
    beam: float | None = Field(None, gt=0)
    draft: float | None = Field(None, gt=0)
    year_built: int | None = Field(None, ge=1900, le=2030)
    flag: str | None = Field(None, max_length=100)
    availability_date: date | None = None
    status: VesselStatus | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)


class VesselResponse(BaseModel):
    """Schema for vessel in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    imo_number: str
    name: str
    ship_owner_id: int
    vessel_type: VesselType
    dwt: float
    loa: float | None = None
    beam: float | None = None
    draft: float | None = None
    year_built: int | None = None
    flag: str | None = None
    availability_date: date | None = None
    status: VesselStatus
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime


class VesselFilter(BaseModel):
    """Filter parameters for vessel queries."""
    vessel_type: VesselType | None = None
    min_dwt: float | None = Field(None, ge=0)
    max_dwt: float | None = Field(None, ge=0)
    max_draft: float | None = Field(None, ge=0)
    status: VesselStatus | None = None
    availability_before: date | None = None
    flag: str | None = None


class VesselNearPortRequest(BaseModel):
    """Request to find vessels near a port."""
    radius_nm: float = Field(default=50.0, gt=0, description="Search radius in nautical miles")
