"""Optimization and vessel matching schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.vessel import VesselType
from app.models.congestion_data import CongestionLevel


class VesselMatchRequest(BaseModel):
    """Input schema for vessel matching."""
    cargo_quantity_mt: float = Field(..., gt=0)
    origin: str = Field(..., min_length=1, max_length=255)
    destination_port_id: int
    required_arrival: datetime | None = None
    preferred_vessel_type: VesselType | None = None
    max_draft: float | None = Field(None, gt=0)
    max_budget: float | None = Field(None, gt=0)


class VesselMatchResult(BaseModel):
    """Single vessel match result."""
    vessel_id: int
    vessel_name: str
    imo_number: str
    vessel_type: VesselType
    dwt: float
    score: float = Field(..., ge=0, le=100)
    estimated_freight_rate: float
    estimated_total_cost: float
    estimated_eta: datetime | None = None
    congestion_risk: CongestionLevel
    distance_nm: float | None = None


class VesselMatchResponse(BaseModel):
    """Response for vessel matching endpoint."""
    matches: list[VesselMatchResult]
    total_candidates: int
    filters_applied: dict


class OptimizationRecommendation(BaseModel):
    """Full optimization recommendation."""
    recommendation: str  # BOOK_NOW, WAIT, REVIEW_ALTERNATIVES
    vessel_id: int | None = None
    vessel_name: str | None = None
    estimated_cost: float
    freight_rate: float
    congestion_risk: CongestionLevel
    best_charter_window_start: datetime | None = None
    best_charter_window_end: datetime | None = None
    reason: str
    confidence: float = Field(..., ge=0, le=1)
    alternatives: list[VesselMatchResult] = []
