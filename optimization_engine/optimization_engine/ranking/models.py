"""
Domain models for vessel ranking (Phase 5).

These models define the configurable ranking weights, per-component
scoring detail, the raw underlying metrics (in native units, for
transparency), and the overall ranked-vessel result.

Ranking never overrides hard feasibility. A vessel excluded by Phase 1
(matching) or Phase 2 (voyage feasibility) is never scored or assigned
a rank — see ``RankingEngine`` in ``engine.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel, Field

from optimization_engine.domain.models import VesselStatus
from optimization_engine.risk.models import RiskCategory


class RankingWeights(BaseModel):
    """Configurable weights for combining ranking components into one score.

    Weights need not sum to 1.0 — the engine normalizes them at
    calculation time so the overall score always stays within 0-100
    regardless of how weights are configured.
    """

    cost: float = Field(default=0.30, ge=0, description="Weight on total voyage cost (lower is better)")
    risk: float = Field(default=0.20, ge=0, description="Weight on overall risk score (lower is better)")
    deadline_buffer: float = Field(
        default=0.20, ge=0, description="Weight on deadline buffer days (higher is better)"
    )
    cargo_suitability: float = Field(
        default=0.10, ge=0, description="Weight on cargo capacity utilization (higher is better)"
    )
    availability: float = Field(
        default=0.10, ge=0, description="Weight on scheduling lead time before the deadline"
    )
    operational_suitability: float = Field(
        default=0.10, ge=0, description="Weight on vessel operational status"
    )

    def as_dict(self) -> dict[str, float]:
        """Return weights keyed by component name, in a fixed, stable order."""
        return {
            "cost": self.cost,
            "risk": self.risk,
            "deadline_buffer": self.deadline_buffer,
            "cargo_suitability": self.cargo_suitability,
            "availability": self.availability,
            "operational_suitability": self.operational_suitability,
        }


class RankingComponentScore(BaseModel):
    """Result of scoring and weighting a single ranking component.

    ``normalized_score`` is always on a 0-100 scale where higher is
    always better, regardless of whether the underlying raw metric is
    "lower is better" (e.g. cost, risk) or "higher is better" (e.g.
    deadline buffer). ``weight`` is the normalized weight actually
    used (sums to 1.0 across all components for a given vessel).
    """

    name: str = Field(..., description="Component name, e.g. 'cost', 'risk'")
    normalized_score: float = Field(
        ..., ge=0, le=100, description="0-100 score for this component; higher is always better"
    )
    weight: float = Field(..., ge=0, le=1, description="Normalized weight applied (0-1)")
    weighted_contribution: float = Field(
        ..., description="normalized_score × weight; contribution to the overall score"
    )
    reason: str = Field(..., description="Human-readable explanation of this component's score")


class RankingRawMetrics(BaseModel):
    """The actual underlying numbers (native units) behind a ranking.

    Provided alongside the scored/weighted ``RankingComponentScore``
    breakdown so a reviewer can see both "what was the real number"
    and "how did that number get scored."
    """

    total_cost: float = Field(..., description="Total voyage cost from Phase 3, in `currency`")
    currency: str = Field(..., description="Currency of total_cost / cost_per_mt")
    cost_per_mt: float = Field(..., description="Total voyage cost divided by cargo quantity")
    deadline_buffer_days: float = Field(
        ..., description="Days between estimated arrival and deadline (Phase 2)"
    )
    overall_risk_score: float = Field(..., ge=0, le=100, description="Overall risk score (Phase 4)")
    risk_category: RiskCategory = Field(..., description="Risk category (Phase 4)")
    cargo_utilization_ratio: float = Field(
        ..., description="cargo.quantity_mt / vessel.cargo_capacity_mt, in (0, 1]"
    )
    availability_lead_days: float = Field(
        ..., description="Days between vessel.available_from and cargo.required_arrival_date"
    )
    vessel_status: VesselStatus = Field(..., description="Vessel operational status")


class RankedVessel(BaseModel):
    """Complete, explainable ranking result for one vessel.

    Infeasible vessels (rejected at Phase 1 or Phase 2) are always
    included in the full result set for transparency, but are never
    scored or ranked: ``rank``, ``overall_score``, ``component_scores``,
    and ``raw_metrics`` are all left empty/``None`` for them. This
    guarantees a high raw metric can never make an infeasible vessel
    look like a viable recommendation.
    """

    rank: Optional[int] = Field(
        default=None, description="1-based rank among feasible vessels; None if not feasible"
    )
    vessel_id: str = Field(..., description="Vessel identifier")
    vessel_name: str = Field(..., description="Vessel name for identification")
    feasible: bool = Field(..., description="Combined Phase 1 + Phase 2 feasibility")

    overall_score: Optional[float] = Field(
        default=None, ge=0, le=100, description="Weighted overall ranking score, 0-100; None if infeasible"
    )
    component_scores: list[RankingComponentScore] = Field(
        default_factory=list, description="Per-component score, weight, and contribution"
    )
    raw_metrics: Optional[RankingRawMetrics] = Field(
        default=None, description="Underlying raw numbers in native units; None if infeasible"
    )

    reasons: list[str] = Field(
        default_factory=list, description="Human-readable reasons driving this result"
    )
    assumptions: list[str] = Field(
        default_factory=list, description="Documented simplifications and methodology notes"
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of when this ranking was performed",
    )
