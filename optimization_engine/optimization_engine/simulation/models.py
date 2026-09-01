"""
Domain models for what-if scenario simulation (Phase 7).

The simulator answers "what happens if...?" by applying one change to
a *copy* of the relevant inputs, re-running the existing Phase 1-5
engines (never duplicating their formulas), and diffing the result
against an unmodified baseline. The baseline inputs passed in are
never mutated — every scenario mutation constructs new model
instances via ``model_copy(update=...)``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from optimization_engine.domain.models import Route, Vessel
from optimization_engine.risk.models import RiskCategory


class ScenarioType(str, Enum):
    """The set of what-if scenarios this simulator supports."""

    FUEL_PRICE_CHANGE = "fuel_price_change"
    FREIGHT_RATE_CHANGE = "freight_rate_change"
    VESSEL_DELAY = "vessel_delay"
    PORT_WAITING_INCREASE = "port_waiting_increase"
    CONGESTION_INCREASE = "congestion_increase"
    WEATHER_DELAY = "weather_delay"
    CARGO_QUANTITY_CHANGE = "cargo_quantity_change"
    DEADLINE_CHANGE = "deadline_change"
    VESSEL_UNAVAILABLE = "vessel_unavailable"
    ALTERNATIVE_VESSEL = "alternative_vessel"
    ALTERNATIVE_ROUTE = "alternative_route"


class ScenarioChange(BaseModel):
    """One what-if change to apply on top of a baseline.

    Only the field(s) relevant to ``scenario_type`` need be set; see
    ``ScenarioSimulator`` for exactly which field each scenario type
    reads. Every other input not touched by the scenario is carried
    over unchanged (as a reference to the same, un-mutated object).
    """

    scenario_type: ScenarioType

    # FUEL_PRICE_CHANGE, FREIGHT_RATE_CHANGE, CARGO_QUANTITY_CHANGE
    multiplier: Optional[float] = Field(
        default=None, gt=0, description="e.g. 1.20 for +20%, 0.90 for -10%"
    )
    # VESSEL_DELAY, PORT_WAITING_INCREASE, WEATHER_DELAY
    additional_days: Optional[float] = Field(default=None, ge=0)
    # CONGESTION_INCREASE
    congestion_delta: Optional[float] = Field(
        default=None, description="Added to congestion_risk_score, clamped to [0, 100]"
    )
    # DEADLINE_CHANGE
    deadline_shift_days: Optional[float] = Field(
        default=None, description="Positive = later/more lenient deadline; negative = earlier/stricter"
    )
    # ALTERNATIVE_VESSEL
    alternative_vessel: Optional[Vessel] = Field(default=None)
    # ALTERNATIVE_ROUTE
    alternative_route: Optional[Route] = Field(default=None)

    description: Optional[str] = Field(
        default=None, description="Optional human-readable label override for this scenario"
    )


class ScenarioSnapshot(BaseModel):
    """A point-in-time result snapshot (baseline or scenario), raw units preserved."""

    feasible: bool
    total_cost: float = Field(..., description="Raw voyage cost, in `currency`")
    currency: str = "USD"
    cost_per_mt: float
    deadline_buffer_days: float
    overall_risk_score: float = Field(..., ge=0, le=100)
    risk_category: RiskCategory


class ScenarioMetricDiff(BaseModel):
    """Absolute and percentage difference for one metric, baseline -> scenario."""

    metric: str
    baseline_value: float
    scenario_value: float
    absolute_difference: float
    percentage_difference: Optional[float] = Field(
        default=None, description="None when baseline_value is 0 (division undefined)"
    )


class ScenarioResult(BaseModel):
    """Complete before/after comparison for one what-if scenario."""

    scenario_type: ScenarioType
    description: str

    vessel_id: str
    vessel_name: str
    route: Optional[Route] = Field(default=None, description="Route the baseline was evaluated on")

    baseline: ScenarioSnapshot
    scenario: ScenarioSnapshot
    metric_diffs: list[ScenarioMetricDiff]

    feasibility_changed: bool = Field(
        ..., description="True if the scenario flips feasible <-> infeasible"
    )
    recommendation_changed: Optional[bool] = Field(
        default=None,
        description=(
            "True/False if fleet context was supplied and the top-ranked "
            "vessel differs between baseline and scenario; None if no fleet "
            "context was supplied (recommendation impact not evaluated)."
        ),
    )
    baseline_top_vessel_id: Optional[str] = Field(default=None)
    scenario_top_vessel_id: Optional[str] = Field(default=None)

    reasons: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
