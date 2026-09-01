"""
Domain models for voyage risk assessment (Phase 4).

These models define the configurable risk factor inputs, configurable
weights, per-factor scoring detail, and the overall risk assessment
output.

All raw factor inputs are **mock/demo values** unless explicitly
supplied by a caller.  None of them are ML predictions — this module
does not build, call, or approximate any machine-learning model.
Where a future ML forecast (e.g. a delay-prediction model owned by
Member 1) would eventually supply a value, the corresponding field is
``Optional`` and clearly documented; when it is not supplied, a
deterministic, clearly labeled placeholder is used instead so that a
mock value is never silently presented as a live prediction.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Risk category
# ---------------------------------------------------------------------------


class RiskCategory(str, Enum):
    """Human-readable risk band derived from the overall 0-100 score."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


# ---------------------------------------------------------------------------
# Configurable inputs
# ---------------------------------------------------------------------------


class RiskFactorInput(BaseModel):
    """Raw, configurable risk inputs for a single vessel/voyage assessment.

    Every field is a **mock/demo value or a documented deterministic
    placeholder** unless supplied by an external system.  Fields that
    will eventually be sourced from another team's system are noted
    below.  All scores are on a common 0-100 scale where 0 = no risk
    and 100 = maximum risk, so they can be combined consistently
    regardless of source.

    Fields left as ``None`` are not fabricated — the engine falls back
    to an explicit, documented default and records this in the
    result's ``assumptions`` and marks the factor as estimated.
    """

    # ── Weather ──────────────────────────────────────────────────────
    weather_risk_score: float = Field(
        default=20.0,
        ge=0,
        le=100,
        description=(
            "Weather/sea-state risk, 0-100. Mock default. Future source: "
            "Geospatial/weather-data integration (Member 4)."
        ),
    )

    # ── Congestion ───────────────────────────────────────────────────
    congestion_risk_score: float = Field(
        default=20.0,
        ge=0,
        le=100,
        description=(
            "Port/route congestion risk, 0-100. Mock default. Future "
            "source: ML congestion forecast (Member 1) or AIS density "
            "(Member 4)."
        ),
    )

    # ── Vessel age ───────────────────────────────────────────────────
    vessel_age_years: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Vessel age in years, if known. If not supplied, a "
            "documented default age-risk score is used instead of "
            "fabricating an age."
        ),
    )

    # ── Vessel condition / maintenance ───────────────────────────────
    vessel_condition_score: float = Field(
        default=15.0,
        ge=0,
        le=100,
        description=(
            "Vessel condition/maintenance risk, 0-100 (higher = worse "
            "condition). Mock default representing a well-maintained "
            "vessel. Future source: Backend maintenance records "
            "(Member 2)."
        ),
    )

    # ── Route hazard / security ──────────────────────────────────────
    route_hazard_score: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description=(
            "Route hazard/security risk (e.g. piracy zones, chokepoints), "
            "0-100. Mock default. Future source: Geospatial routing "
            "layer (Member 4)."
        ),
    )

    # ── Port restriction ──────────────────────────────────────────────
    port_restriction_score: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description=(
            "Destination port restriction risk (tidal windows, draft "
            "restrictions, regulatory holds), 0-100. Mock default. "
            "Future source: Backend port-authority data (Member 2)."
        ),
    )

    # ── Cargo hazard ──────────────────────────────────────────────────
    cargo_hazard_override: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "Explicit cargo hazard risk, 0-100, if known. If not "
            "supplied, derived deterministically from "
            "``Cargo.hazardous``."
        ),
    )

    # ── Documentation / compliance ────────────────────────────────────
    documentation_compliance_score: float = Field(
        default=10.0,
        ge=0,
        le=100,
        description=(
            "Documentation/compliance risk (missing certificates, "
            "flag-state issues), 0-100. Mock default. Future source: "
            "Backend compliance records (Member 2)."
        ),
    )

    # ── Predicted delay ────────────────────────────────────────────────
    predicted_delay_risk_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "Predicted delay risk, 0-100, supplied by an external ML "
            "forecast (Member 1). This engine NEVER fabricates this "
            "value. If not supplied, a deterministic proxy derived "
            "from the voyage's deadline buffer is used instead and "
            "clearly marked as an estimate, not a prediction."
        ),
    )

    # ── Historical incidents ───────────────────────────────────────────
    historical_incident_score: float = Field(
        default=5.0,
        ge=0,
        le=100,
        description=(
            "Historical incident risk for this vessel/route, 0-100. "
            "Mock default. Future source: Backend incident records "
            "(Member 2)."
        ),
    )


class RiskWeights(BaseModel):
    """Configurable weights for combining risk factors into one score.

    Weights need not sum to 1.0 — the engine normalizes them at
    calculation time so the overall score always stays within 0-100
    regardless of how weights are configured. This keeps the weights
    transparent and independently tunable.
    """

    weather: float = Field(default=0.10, ge=0)
    congestion: float = Field(default=0.10, ge=0)
    vessel_age: float = Field(default=0.10, ge=0)
    vessel_condition: float = Field(default=0.15, ge=0)
    route_hazard: float = Field(default=0.10, ge=0)
    port_restriction: float = Field(default=0.05, ge=0)
    cargo_hazard: float = Field(default=0.10, ge=0)
    documentation_compliance: float = Field(default=0.10, ge=0)
    predicted_delay: float = Field(default=0.15, ge=0)
    historical_incident: float = Field(default=0.05, ge=0)

    def as_dict(self) -> dict[str, float]:
        """Return weights keyed by factor name, in a fixed, stable order."""
        return {
            "weather": self.weather,
            "congestion": self.congestion,
            "vessel_age": self.vessel_age,
            "vessel_condition": self.vessel_condition,
            "route_hazard": self.route_hazard,
            "port_restriction": self.port_restriction,
            "cargo_hazard": self.cargo_hazard,
            "documentation_compliance": self.documentation_compliance,
            "predicted_delay": self.predicted_delay,
            "historical_incident": self.historical_incident,
        }


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class RiskFactorScore(BaseModel):
    """Result of scoring and weighting a single risk factor.

    ``raw_score`` is always on the common 0-100 scale, after any
    deterministic derivation/fallback has been applied. ``weight`` is
    the *normalized* weight actually used (sums to 1.0 across all
    factors in a given assessment).
    """

    name: str = Field(..., description="Factor name, e.g. 'weather', 'vessel_age'")
    raw_score: float = Field(..., ge=0, le=100, description="Factor risk score, 0-100")
    weight: float = Field(..., ge=0, le=1, description="Normalized weight applied (0-1)")
    weighted_contribution: float = Field(
        ..., description="raw_score × weight; contribution to the overall score"
    )
    is_estimated: bool = Field(
        default=False,
        description=(
            "True if this factor's raw_score came from a documented "
            "fallback/default because no explicit input was supplied."
        ),
    )
    reason: str = Field(..., description="Human-readable explanation of this factor's score")


class RiskAssessmentResult(BaseModel):
    """Complete, explainable risk assessment for one vessel on one voyage.

    ``overall_risk_score`` is always in [0, 100] regardless of how
    ``RiskWeights`` is configured, because weights are normalized
    before being applied.
    """

    vessel_id: str = Field(..., description="Vessel identifier")
    vessel_name: str = Field(..., description="Vessel name for identification")
    cargo_id: str = Field(..., description="Cargo requirement identifier")
    route_id: Optional[str] = Field(
        default=None, description="Route identifier, if a route was supplied"
    )

    overall_risk_score: float = Field(
        ..., ge=0, le=100, description="Weighted overall risk score, 0-100"
    )
    risk_category: RiskCategory = Field(
        ..., description="Risk band derived from overall_risk_score"
    )
    factor_scores: list[RiskFactorScore] = Field(
        ..., description="Per-factor score, weight, and weighted contribution"
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Top-level human-readable reasons driving the overall score",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Documented simplifications, mock-data, and fallback disclaimers",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of when this assessment was performed",
    )
