"""
Domain models for multi-route decision support (Phase 8).

``RouteCandidate`` bundles everything about one candidate route into a
single typed object — the Phase 5 ranked shortlist for that route, and
(optionally) the underlying risk results needed to compare secondary
factors like congestion, and an emissions figure once Phase 9 is
wired in. Route identity is always the typed ``Route`` object on the
candidate, never a bare route-id string used as a dict key.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel, Field

from optimization_engine.domain.models import Route
from optimization_engine.ranking.models import RankedVessel
from optimization_engine.risk.models import RiskAssessmentResult, RiskCategory


class RouteCandidate(BaseModel):
    """A route paired with its own ranked vessel shortlist.

    Produced by running the full matching -> voyage -> economics ->
    risk -> ranking pipeline once per candidate route. Route identity
    is always a typed ``Route`` object, never a bare string key, so
    downstream consumers (decision engine, multi-route comparison)
    never lose track of which physical route a result belongs to.
    """

    route: Route = Field(..., description="The route this shortlist was computed for")
    ranked_vessels: list[RankedVessel] = Field(
        default_factory=list,
        description="Phase 5 output for this route (feasible and infeasible vessels)",
    )
    risk_results: list[RiskAssessmentResult] = Field(
        default_factory=list,
        description=(
            "Optional Phase 4 results for this route's vessels, needed only to "
            "extract secondary factor detail (e.g. congestion) for route "
            "comparison. If omitted, congestion is simply not compared."
        ),
    )
    emissions_co2_kg: Optional[float] = Field(
        default=None,
        description="Total CO2 for this route's best vessel, kg — Phase 9 hook. Optional.",
    )


class RouteWeights(BaseModel):
    """Configurable weights for comparing routes.

    Weights need not sum to 1.0 — they are normalized at calculation
    time over whichever components actually have data for the current
    batch (congestion and emissions are dropped from the comparison,
    not defaulted to a fabricated value, when any route in the batch
    is missing that data).
    """

    cost: float = Field(default=0.35, ge=0)
    risk: float = Field(default=0.25, ge=0)
    deadline_buffer: float = Field(default=0.25, ge=0)
    congestion: float = Field(default=0.10, ge=0, description="Only used if every feasible route has congestion data")
    emissions: float = Field(default=0.05, ge=0, description="Only used if every feasible route has emissions data")

    def as_dict(self) -> dict[str, float]:
        return {
            "cost": self.cost,
            "risk": self.risk,
            "deadline_buffer": self.deadline_buffer,
            "congestion": self.congestion,
            "emissions": self.emissions,
        }


class RouteComponentScore(BaseModel):
    """One scored, weighted comparison component for a route."""

    name: str
    normalized_score: float = Field(..., ge=0, le=100, description="Higher is always better")
    weight: float = Field(..., ge=0, le=1, description="Normalized weight actually used")
    weighted_contribution: float
    reason: str


class RouteMetrics(BaseModel):
    """The real, raw numbers behind a route comparison — never normalized away."""

    route: Route
    feasible: bool
    best_vessel_id: Optional[str] = None
    best_vessel_name: Optional[str] = None
    deadline_buffer_days: Optional[float] = None
    total_cost: Optional[float] = None
    cost_per_mt: Optional[float] = None
    overall_risk_score: Optional[float] = Field(default=None, ge=0, le=100)
    risk_category: Optional[RiskCategory] = None
    congestion_risk_score: Optional[float] = Field(
        default=None, description="From the best vessel's risk breakdown, if risk_results was supplied"
    )
    emissions_co2_kg: Optional[float] = None
    num_feasible_vessels: int = 0


class RankedRoute(BaseModel):
    """Complete, explainable comparison result for one route.

    A route with no feasible vessel is never scored or ranked — the
    same hard-constraint discipline as Phase 5's vessel ranking,
    applied one level up.
    """

    rank: Optional[int] = Field(default=None, description="1-based rank among feasible routes")
    route: Route
    feasible: bool

    overall_score: Optional[float] = Field(default=None, ge=0, le=100)
    component_scores: list[RouteComponentScore] = Field(default_factory=list)
    raw_metrics: Optional[RouteMetrics] = Field(default=None)

    reasons: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

