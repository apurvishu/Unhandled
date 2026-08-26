"""Port schemas with coordinate validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PortCreate(BaseModel):
    """Schema for creating a port."""
    name: str = Field(..., min_length=1, max_length=255)
    country: str = Field(..., min_length=1, max_length=100)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    max_draft: float | None = Field(None, gt=0)
    max_loa: float | None = Field(None, gt=0)
    cargo_capacity: float | None = Field(None, gt=0)


class PortUpdate(BaseModel):
    """Schema for updating a port."""
    name: str | None = Field(None, min_length=1, max_length=255)
    country: str | None = Field(None, min_length=1, max_length=100)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    max_draft: float | None = Field(None, gt=0)
    max_loa: float | None = Field(None, gt=0)
    cargo_capacity: float | None = Field(None, gt=0)


class PortResponse(BaseModel):
    """Schema for port in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str
    latitude: float
    longitude: float
    max_draft: float | None = None
    max_loa: float | None = None
    cargo_capacity: float | None = None
    created_at: datetime
