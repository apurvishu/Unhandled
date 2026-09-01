"""
Domain models for the final orchestration layer (Phase 10).

IMPORTANT NAMING NOTE: this module lives in `optimization_engine/optimization/`
to match the agreed project structure, but nothing here performs
mathematical optimization. There are no decision variables, objective
function, or constraint set of the kind OR-Tools (or any solver) would
require — see Phase 6/7/8 rules. What this module does is
**orchestrate** the existing, already-tested engines (Phases 1-9) into
one deterministic pipeline and package their output as a single
``FinalRecommendation``. If a genuine mathematical optimization
problem is defined in the future, it belongs in its own module with
its own name — this one should not be repurposed for it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel, Field

from optimization_engine.decision.models import DecisionAction, DecisionAlternative
from optimization_engine.domain.models import Cargo, Port, Route
from optimization_engine.emissions.models import EmissionsResult
from optimization_engine.ranking.models import RankedVessel
from optimization_engine.risk.models import RiskCategory


class AlternativeRouteInput(BaseModel):
    """One alternative route to evaluate alongside the primary route.

    ``origin_port``/``destination_port`` are optional and, if omitted,
    fall back to the primary route's ports.

    IMPORTANT — cargo/route matching: Phase 2's ``VoyageFeasibilityEngine``
    validates that a route's origin AND destination match the
    ``Cargo`` object's own ``origin_port``/``destination_port`` fields
    exactly (this existing Phase 1-2 validation is preserved, not
    weakened, here). If an alternative route has a different origin
    or destination than the primary cargo, supply a matching ``cargo``
    here (same quantity/type/deadline, but with ``origin_port``/
    ``destination_port`` set to match this route) — otherwise Phase 2
    will raise a clear ``ValueError`` when this route is evaluated.
    This is the correct, explicit way to compare genuinely different
    origin/destination combinations for the same underlying shipment
    requirement (e.g. "source via Shanghai vs. Singapore, discharge at
    Paradip vs. Visakhapatnam") without weakening Phase 2's guarantee
    that a route always matches the cargo it claims to serve.
    """

    route: Route
    origin_port: Optional[Port] = Field(
        default=None, description="Falls back to the primary run's origin_port if omitted"
    )
    destination_port: Optional[Port] = Field(
        default=None, description="Falls back to the primary run's destination_port if omitted"
    )
    cargo: Optional[Cargo] = Field(
        default=None,
        description=(
            "Required if this route's origin/destination differ from the primary "
            "cargo's; must have origin_port/destination_port matching this route. "
            "Falls back to the primary cargo if omitted."
        ),
    )


class FinalRecommendation(BaseModel):
    """The complete, explainable output of one end-to-end run.

    Raw physical/economic values (``expected_total_cost``, ``cost_per_mt``,
    ``deadline_buffer_days``, ``risk_score``) are always the real
    figures from the underlying Phase 3/4 results — never replaced by
    a normalized ranking or decision-comparison score. An infeasible
    outcome always has ``selected_vessel_id``/``selected_route`` as
    ``None`` — this engine never selects an infeasible vessel or route.
    """

    cargo_id: str
    feasible: bool = Field(..., description="Whether any feasible vessel/route combination existed")
    recommended_action: DecisionAction

    selected_vessel_id: Optional[str] = None
    selected_vessel_name: Optional[str] = None
    selected_route: Optional[Route] = None

    estimated_arrival: Optional[datetime] = None
    deadline_buffer_days: Optional[float] = None

    expected_total_cost: Optional[float] = Field(default=None, description="Raw dollar cost, never normalized")
    cost_per_mt: Optional[float] = None
    risk_score: Optional[float] = Field(default=None, ge=0, le=100)
    risk_category: Optional[RiskCategory] = None
    emissions: Optional[EmissionsResult] = Field(
        default=None, description="Optional Phase 9 output; None if compute_emissions=False or unavailable"
    )

    alternatives: list[DecisionAlternative] = Field(
        default_factory=list, description="Every alternative the decision layer considered"
    )
    ranked_vessels_on_selected_route: list[RankedVessel] = Field(
        default_factory=list,
        description="Full Phase 5 ranking on the selected (or primary, if infeasible) route, for transparency",
    )
    expected_savings: Optional[float] = None

    explanation: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
