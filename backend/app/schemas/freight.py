"""Freight rate and forecast schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.vessel import VesselType


class FreightRateCreate(BaseModel):
    """Schema for creating a freight rate entry."""
    origin: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    vessel_type: VesselType
    rate: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=10)
    rate_date: date
    source: str | None = None


class FreightRateResponse(BaseModel):
    """Schema for freight rate in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    origin: str
    destination: str
    vessel_type: VesselType
    rate: float
    currency: str
    rate_date: date
    source: str | None = None
    created_at: datetime


class FreightForecastRequest(BaseModel):
    """Schema for requesting a freight forecast."""
    origin: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    vessel_type: VesselType
    forecast_horizon_days: int = Field(default=30, ge=1, le=365)


class FreightForecastResponse(BaseModel):
    """Schema for freight forecast response."""
    predicted_rate: float
    currency: str = "USD"
    unit: str = "MT"
    confidence: float = Field(..., ge=0, le=1)
    lower_bound: float
    upper_bound: float
    trend: str  # INCREASING, DECREASING, STABLE
    recommendation: str  # BOOK_NOW, WAIT, NEUTRAL
    model_version: str
    forecast_date: date
