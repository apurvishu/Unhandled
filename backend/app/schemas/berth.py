"""Berth schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.berth import BerthStatus


class BerthCreate(BaseModel):
    """Schema for creating a berth."""
    name: str = Field(..., min_length=1, max_length=255)
    max_draft: float | None = Field(None, gt=0)
    max_loa: float | None = Field(None, gt=0)
    cargo_handling_rate: float | None = Field(None, gt=0, description="MT per hour")
    status: BerthStatus = BerthStatus.AVAILABLE
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)


class BerthUpdate(BaseModel):
    """Schema for updating a berth."""
    name: str | None = Field(None, min_length=1, max_length=255)
    max_draft: float | None = Field(None, gt=0)
    max_loa: float | None = Field(None, gt=0)
    cargo_handling_rate: float | None = Field(None, gt=0)
    status: BerthStatus | None = None


class BerthResponse(BaseModel):
    """Schema for berth in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    port_id: int
    name: str
    max_draft: float | None = None
    max_loa: float | None = None
    cargo_handling_rate: float | None = None
    status: BerthStatus
    created_at: datetime
