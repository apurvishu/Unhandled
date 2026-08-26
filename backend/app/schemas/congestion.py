"""Congestion prediction schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.congestion_data import CongestionLevel


class CongestionDataResponse(BaseModel):
    """Schema for congestion data in responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    port_id: int
    timestamp: datetime
    vessels_waiting: int | None = None
    vessels_at_berth: int | None = None
    average_waiting_time: float | None = None
    berth_utilization: float | None = None
    congestion_level: CongestionLevel | None = None
    predicted_waiting_time: float | None = None


class CongestionPredictionRequest(BaseModel):
    """Schema for requesting a congestion prediction."""
    port_id: int
    horizon_hours: int = Field(default=24, ge=1, le=168, description="Prediction horizon in hours")


class CongestionPredictionResponse(BaseModel):
    """Schema for congestion prediction response."""
    port_id: int
    congestion_level: CongestionLevel
    predicted_waiting_time: float  # hours
    berth_utilization: float  # percentage
    vessels_expected: int
    confidence: float = Field(..., ge=0, le=1)
    prediction_horizon_hours: int
