"""
Domain models for charter optimization / decision-making (Phase 6).

These models turn ranked feasible vessels (Phase 5), optionally across
multiple candidate routes (Phase 8's ``RouteCandidate``), into an
actual charter decision: book now, wait, or switch to a different
vessel or route.

Design principles enforced by this module:
    - **Ranking != optimization.** ``RankedVessel.overall_score``
      answers "which candidate is better?"; this module answers "what
      should we actually do?" by comparing every relevant alternative
      on one commensurable metric (see ``DecisionAlternative.adjusted_cost``).
    - **No premature stopping.** Every relevant alternative (book now
      with each risk-acceptable vessel, wait if a forecast is
      available, book on each alternative route) is built and compared
      — not evaluated as a priority cascade that stops at the first
      match.
    - **Typed route identity.** Routes are always represented as
      ``Route`` objects, never as bare route-id strings in a dict key.
    - **No fabricated ML.** ``FreightForecastInput`` is the one typed
      contract for external freight forecasts. It is always optional;
      the engine is capable of receiving a mock-populated instance now
      and Member 1's real ML output later, through the same contract.
    - **Raw values preserved.** ``expected_total_cost`` is always the
      real, un-normalized dollar figure. ``adjusted_cost`` is a
      *comparison* metric (it may add a monetized risk term) and is
      never presented as the "real" cost.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from optimization_engine.domain.models import Route
from optimization_engine.risk.models import RiskCategory


class DecisionAction(str, Enum):
    """The set of charter decisions this engine can recommend."""

    BOOK_NOW = "book_now"
    WAIT = "wait"
    SELECT_ALTERNATIVE_VESSEL = "select_alternative_vessel"
    SELECT_ALTERNATIVE_ROUTE = "select_alternative_route"
    NO_FEASIBLE_OPTION = "no_feasible_option"


class FreightForecastInput(BaseModel):
    """Typed contract for an external freight-rate forecast.

    This is the ONE shape the decision engine understands for "what
    might the freight rate do if we wait." Today it is populated with
    mock/demo values (see ``fixtures.py``); later, Member 1's ML
    freight-forecasting model can populate the exact same contract.
    The engine never constructs this itself — it is always supplied
    by the caller, and ``source`` discloses its provenance.
    """

    current_freight_rate_per_mt: float = Field(
        ..., ge=0, description="Current freight/charter rate, USD/MT, for reference"
    )
    predicted_freight_rate_per_mt: float = Field(
        ..., ge=0, description="Forecast freight rate, USD/MT"
    )
    forecast_horizon_days: float = Field(
        ..., ge=0, description="Days ahead this forecast applies to (used as the wait duration)"
    )
    confidence: Optional[float] = Field(
        default=None, ge=0, le=1, description="Forecast confidence, 0-1, if supplied"
    )
    lower_bound_per_mt: Optional[float] = Field(default=None, ge=0)
    upper_bound_per_mt: Optional[float] = Field(default=None, ge=0)
    source: str = Field(
        default="mock",
        description=(
            "Provenance label, e.g. 'mock' (demo data owned by this module) or "
            "'member1_ml' (Member 1's freight-forecasting model). Never treated "
            "as live data unless explicitly labeled as such."
        ),
    )


class DecisionInput(BaseModel):
    """Configurable policy thresholds for the decision engine.

    Every threshold here is a deterministic policy knob owned by this
    engine — not a forecast. The only externally-sourced, ML-shaped
    input anywhere in this module is ``freight_forecast``.
    """

    max_acceptable_risk_score: float = Field(
        default=70.0,
        ge=0,
        le=100,
        description=(
            "Vessels with overall risk above this threshold are excluded from "
            "the 'book now' comparison pool unless no vessel meets it, in "
            "which case the least-risky feasible vessel is used as a fallback "
            "(flagged in the result)."
        ),
    )
    risk_cost_per_point: float = Field(
        default=0.0,
        ge=0,
        description=(
            "USD imputed per risk-score point, used ONLY to make risk "
            "commensurable with dollar cost when comparing alternatives "
            "(adjusted_cost = total_cost + risk_score * risk_cost_per_point). "
            "Default 0 means risk acts purely as the hard gate above, with no "
            "effect on cost comparisons among gate-passing options."
        ),
    )
    waiting_cost_per_day: float = Field(
        default=5_000.0, ge=0, description="Mock cost of vessel/cargo waiting per day, USD."
    )
    congestion_cost_per_day: float = Field(
        default=0.0, ge=0, description="Mock additional congestion cost per waiting day, USD."
    )
    min_acceptable_deadline_buffer_days: float = Field(
        default=0.0,
        description="Minimum deadline buffer that must remain after waiting for WAIT to be viable.",
    )
    min_confidence_threshold: float = Field(
        default=0.6, ge=0, le=1, description="Minimum forecast confidence required to act on WAIT."
    )
    min_switch_improvement_pct: float = Field(
        default=0.0,
        ge=0,
        description=(
            "Minimum percentage improvement in adjusted_cost required before "
            "switching away from the top-ranked vessel's BOOK_NOW option "
            "(prevents churn from negligible numerical differences)."
        ),
    )
    freight_forecast: Optional[FreightForecastInput] = Field(
        default=None,
        description=(
            "External freight-rate forecast. If omitted, WAIT is never "
            "constructed as an alternative — there is no basis to recommend "
            "waiting without a forecast."
        ),
    )


class WaitVsBookComparison(BaseModel):
    """The numbers behind the WAIT alternative, fully visible."""

    current_cost_per_mt: float
    predicted_cost_per_mt: float
    predicted_savings_per_mt: float
    predicted_total_savings: float
    expected_wait_days: float
    expected_waiting_cost: float
    net_expected_benefit_of_waiting: float = Field(
        ..., description="Raw-dollar comparison: current total cost minus projected wait total cost"
    )
    deadline_buffer_after_wait_days: float
    meets_confidence_threshold: Optional[bool] = None


class DecisionAlternative(BaseModel):
    """One fully-evaluated alternative, shown alongside the winner for transparency.

    Every alternative the engine considered is included here — not
    just the recommended one — so "why not the alternatives" (Phase 12)
    can be answered directly from this list.
    """

    action: DecisionAction
    vessel_id: Optional[str] = None
    vessel_name: Optional[str] = None
    route: Optional[Route] = Field(
        default=None, description="Typed route this alternative applies to, if known"
    )
    expected_total_cost: float = Field(..., description="Raw, real dollar cost — never normalized")
    adjusted_cost: float = Field(
        ..., description="Comparison metric: total_cost plus any monetized risk/waiting terms"
    )
    risk_score: Optional[float] = Field(default=None, ge=0, le=100)
    deadline_buffer_days: Optional[float] = None
    feasible_alternative: bool = Field(
        default=True, description="Whether this alternative clears all policy gates"
    )
    notes: str = Field(default="", description="Short human-readable note on this alternative")


class DecisionResult(BaseModel):
    """Complete, explainable charter decision, with every alternative shown."""

    recommended_action: DecisionAction

    selected_vessel_id: Optional[str] = None
    selected_vessel_name: Optional[str] = None
    selected_route: Optional[Route] = Field(
        default=None, description="Typed route object for the recommended action, if applicable"
    )

    expected_total_cost: Optional[float] = Field(
        default=None, description="Raw, real dollar cost of the recommended action"
    )
    cost_per_mt: Optional[float] = None
    adjusted_cost: Optional[float] = Field(
        default=None, description="The comparison metric that won; see DecisionAlternative"
    )

    wait_vs_book_comparison: Optional[WaitVsBookComparison] = None
    expected_savings: Optional[float] = Field(
        default=None,
        description=(
            "Raw-dollar difference between the recommended action's "
            "expected_total_cost and the next-best alternative's. Positive "
            "means cheaper; negative means the recommendation cost more in "
            "raw dollars but was preferred for other reasons (e.g. risk)."
        ),
    )

    deadline_impact_days: Optional[float] = None
    risk_score: Optional[float] = Field(default=None, ge=0, le=100)
    risk_category: Optional[RiskCategory] = None

    alternatives: list[DecisionAlternative] = Field(
        default_factory=list, description="Every alternative considered, including the winner"
    )

    reasons: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
