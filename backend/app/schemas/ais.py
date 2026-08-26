"""AIS position and vessel tracking schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AISPositionResponse(BaseModel):
    """Schema for AIS position in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    vessel_id: int
    timestamp: datetime
    latitude: float
    longitude: float
    speed: float | None = None
    course: float | None = None
    heading: float | None = None
    destination: str | None = None
    eta: datetime | None = None
    navigation_status: str | None = None


class VesselTrackResponse(BaseModel):
    """Schema for vessel track (list of positions)."""
    vessel_id: int
    positions: list[AISPositionResponse]
    total_positions: int


class VesselPositionUpdate(BaseModel):
    """Schema for updating a vessel's AIS position."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: float | None = Field(None, ge=0)
    course: float | None = Field(None, ge=0, le=360)
    heading: float | None = Field(None, ge=0, le=360)
    destination: str | None = None
    eta: datetime | None = None
    navigation_status: str | None = None
