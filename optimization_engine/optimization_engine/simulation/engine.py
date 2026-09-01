"""
What-If Scenario Simulation Engine (Phase 7).

Reuses the existing Phase 1 (matching), Phase 2 (voyage feasibility),
Phase 3 (economics), and Phase 4 (risk) engines to compute both a
baseline and a scenario result, then diffs them. No formula from any
earlier phase is duplicated here.

The baseline inputs (vessel, cargo, route, cost input, risk input)
passed into ``simulate()`` are **never mutated** — every scenario
mutation is applied to a *new* model instance via ``model_copy``.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

from optimization_engine.domain.models import Cargo, Port, Route, Vessel, VesselStatus
from optimization_engine.economics.engine import VoyageEconomicsEngine
from optimization_engine.economics.models import VoyageCostBreakdown, VoyageCostInput
from optimization_engine.matching.engine import MatchingEngine
from optimization_engine.ranking.engine import RankingEngine
from optimization_engine.ranking.models import RankingWeights
from optimization_engine.risk.engine import RiskEngine
from optimization_engine.risk.models import RiskAssessmentResult, RiskFactorInput, RiskWeights
from optimization_engine.simulation.models import (
    ScenarioChange,
    ScenarioMetricDiff,
    ScenarioResult,
    ScenarioSnapshot,
    ScenarioType,
)
from optimization_engine.voyage.engine import VoyageFeasibilityEngine

_BASELINE_ASSUMPTIONS: list[str] = [
    "The simulator reuses the existing matching, voyage, economics, and risk "
    "engines unmodified; no formula is duplicated here.",
    "Baseline inputs are never mutated — every scenario mutation constructs a "
    "new copy via model_copy(update=...).",
    "WEATHER_DELAY and VESSEL_DELAY are modeled differently: a weather delay "
    "slows the passage (an effective speed reduction, same departure date); a "
    "vessel delay pushes the departure date back by the same number of days.",
    "PORT_WAITING_INCREASE affects only cost inputs (berth/maintenance days); "
    "Phase 2's ETA calculation does not model destination port waiting time.",
    "Waiting for an alternative vessel/route to become available is not "
    "modeled — ALTERNATIVE_VESSEL and ALTERNATIVE_ROUTE compare against a "
    "wholesale substitute, evaluated fresh.",
]


class ScenarioSimulator:
    """Computes deterministic before/after comparisons for what-if scenarios.

    Usage::

        simulator = ScenarioSimulator()
        result = simulator.simulate(
            scenario=ScenarioChange(scenario_type=ScenarioType.FUEL_PRICE_CHANGE, multiplier=1.2),
            vessel=vessel, cargo=cargo, route=route,
            origin_port=origin_port, destination_port=destination_port,
            cost_input=cost_input,
        )
    """

    def __init__(self) -> None:
        self._matching = MatchingEngine()
        self._voyage = VoyageFeasibilityEngine()
        self._economics = VoyageEconomicsEngine()
        self._risk = RiskEngine()
        self._ranking = RankingEngine()

    def simulate(
        self,
        scenario: ScenarioChange,
        vessel: Vessel,
        cargo: Cargo,
        route: Route,
        origin_port: Port,
        destination_port: Port,
        cost_input: VoyageCostInput,
        *,
        risk_input: Optional[RiskFactorInput] = None,
        risk_weights: Optional[RiskWeights] = None,
        other_voyage_results: Optional[list] = None,
        other_cost_results: Optional[list[VoyageCostBreakdown]] = None,
        other_risk_results: Optional[list[RiskAssessmentResult]] = None,
        ranking_weights: Optional[RankingWeights] = None,
    ) -> ScenarioResult:
        """Run one what-if scenario and return the full before/after comparison.

        Args:
            scenario: The change to apply.
            vessel, cargo, route, origin_port, destination_port, cost_input:
                Baseline inputs. Never mutated.
            risk_input: Optional baseline risk factor inputs.
            risk_weights: Optional risk weight configuration.
            other_voyage_results, other_cost_results, other_risk_results:
                Optional Phase 2/3/4 results for the *rest* of the fleet
                (unaffected by this scenario). Supplying all three
                enables ``recommendation_changed`` to be computed by
                re-ranking the full batch before and after the scenario.
            ranking_weights: Optional ranking weight configuration, used
                only if fleet context is supplied.

        Returns:
            A ``ScenarioResult`` with baseline, scenario, diffs, and
            (if fleet context was supplied) recommendation-change info.
        """
        baseline_voyage, baseline_cost, baseline_risk = self._evaluate(
            vessel, cargo, route, origin_port, destination_port, cost_input, risk_input, risk_weights
        )

        s_vessel, s_cargo, s_route, s_cost_input, s_risk_input = self._apply_scenario(
            scenario, vessel, cargo, route, cost_input, risk_input
        )
        scenario_voyage, scenario_cost, scenario_risk = self._evaluate(
            s_vessel, s_cargo, s_route, origin_port, destination_port, s_cost_input, s_risk_input, risk_weights
        )

        baseline_snapshot = self._snapshot(baseline_voyage, baseline_cost, baseline_risk)
        scenario_snapshot = self._snapshot(scenario_voyage, scenario_cost, scenario_risk)
        diffs = self._diff_snapshots(baseline_snapshot, scenario_snapshot)

        recommendation_changed = None
        baseline_top_id = None
        scenario_top_id = None
        if other_voyage_results is not None and other_cost_results is not None and other_risk_results is not None:
            recommendation_changed, baseline_top_id, scenario_top_id = self._check_recommendation_change(
                baseline_voyage, baseline_cost, baseline_risk,
                scenario_voyage, scenario_cost, scenario_risk,
                other_voyage_results, other_cost_results, other_risk_results,
                cargo, ranking_weights,
            )

        reasons = self._build_reasons(scenario, diffs, baseline_snapshot, scenario_snapshot)

        return ScenarioResult(
            scenario_type=scenario.scenario_type,
            description=scenario.description or scenario.scenario_type.value.replace("_", " "),
            vessel_id=vessel.vessel_id,
            vessel_name=vessel.vessel_name,
            route=route,
            baseline=baseline_snapshot,
            scenario=scenario_snapshot,
            metric_diffs=diffs,
            feasibility_changed=baseline_snapshot.feasible != scenario_snapshot.feasible,
            recommendation_changed=recommendation_changed,
            baseline_top_vessel_id=baseline_top_id,
            scenario_top_vessel_id=scenario_top_id,
            reasons=reasons,
            assumptions=list(_BASELINE_ASSUMPTIONS),
        )

    # ------------------------------------------------------------------
    # Evaluation (reuses Phase 1/2/3/4 engines, unmodified)
    # ------------------------------------------------------------------

    def _evaluate(
        self,
        vessel: Vessel,
        cargo: Cargo,
        route: Route,
        origin_port: Port,
        destination_port: Port,
        cost_input: VoyageCostInput,
        risk_input: Optional[RiskFactorInput],
        risk_weights: Optional[RiskWeights],
    ):
        match_result = self._matching.match_vessels(cargo, [vessel], origin_port, destination_port)[0]
        voyage_result = self._voyage.evaluate(match_result, route, cargo)
        cost_breakdown = self._economics.calculate(voyage_result, cargo, cost_input)
        risk_result = self._risk.assess_voyage(
            voyage_result, cargo, risk_input=risk_input, weights=risk_weights
        )
        return voyage_result, cost_breakdown, risk_result

    # ------------------------------------------------------------------
    # Scenario mutation (never mutates the originals)
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_scenario(
        scenario: ScenarioChange,
        vessel: Vessel,
        cargo: Cargo,
        route: Route,
        cost_input: VoyageCostInput,
        risk_input: Optional[RiskFactorInput],
    ) -> tuple[Vessel, Cargo, Route, VoyageCostInput, Optional[RiskFactorInput]]:
        st = scenario.scenario_type
        risk_input = risk_input if risk_input is not None else RiskFactorInput()

        if st == ScenarioType.FUEL_PRICE_CHANGE:
            if scenario.multiplier is None:
                raise ValueError("FUEL_PRICE_CHANGE requires 'multiplier'.")
            cost_input = cost_input.model_copy(
                update={"fuel_price_per_mt": cost_input.fuel_price_per_mt * scenario.multiplier}
            )

        elif st == ScenarioType.FREIGHT_RATE_CHANGE:
            if scenario.multiplier is None:
                raise ValueError("FREIGHT_RATE_CHANGE requires 'multiplier'.")
            cost_input = cost_input.model_copy(
                update={"freight_rate_per_mt": cost_input.freight_rate_per_mt * scenario.multiplier}
            )

        elif st == ScenarioType.VESSEL_DELAY:
            if scenario.additional_days is None:
                raise ValueError("VESSEL_DELAY requires 'additional_days'.")
            vessel = vessel.model_copy(
                update={"available_from": vessel.available_from + timedelta(days=scenario.additional_days)}
            )

        elif st == ScenarioType.PORT_WAITING_INCREASE:
            if scenario.additional_days is None:
                raise ValueError("PORT_WAITING_INCREASE requires 'additional_days'.")
            cost_input = cost_input.model_copy(
                update={"port_days": cost_input.port_days + scenario.additional_days}
            )

        elif st == ScenarioType.CONGESTION_INCREASE:
            if scenario.congestion_delta is None:
                raise ValueError("CONGESTION_INCREASE requires 'congestion_delta'.")
            new_score = risk_input.congestion_risk_score + scenario.congestion_delta
            risk_input = risk_input.model_copy(
                update={"congestion_risk_score": max(0.0, min(100.0, new_score))}
            )

        elif st == ScenarioType.WEATHER_DELAY:
            if scenario.additional_days is None:
                raise ValueError("WEATHER_DELAY requires 'additional_days'.")
            original_sailing_hours = route.distance_nm / vessel.speed_knots
            target_sailing_hours = original_sailing_hours + scenario.additional_days * 24.0
            if target_sailing_hours <= 0:
                raise ValueError("WEATHER_DELAY would result in non-positive sailing time.")
            new_speed = route.distance_nm / target_sailing_hours
            vessel = vessel.model_copy(update={"speed_knots": new_speed})
            bumped_weather = min(100.0, risk_input.weather_risk_score + 20.0)
            risk_input = risk_input.model_copy(update={"weather_risk_score": bumped_weather})

        elif st == ScenarioType.CARGO_QUANTITY_CHANGE:
            if scenario.multiplier is None:
                raise ValueError("CARGO_QUANTITY_CHANGE requires 'multiplier'.")
            cargo = cargo.model_copy(update={"quantity_mt": cargo.quantity_mt * scenario.multiplier})

        elif st == ScenarioType.DEADLINE_CHANGE:
            if scenario.deadline_shift_days is None:
                raise ValueError("DEADLINE_CHANGE requires 'deadline_shift_days'.")
            cargo = cargo.model_copy(
                update={
                    "required_arrival_date": cargo.required_arrival_date
                    + timedelta(days=scenario.deadline_shift_days)
                }
            )

        elif st == ScenarioType.VESSEL_UNAVAILABLE:
            vessel = vessel.model_copy(update={"status": VesselStatus.UNDER_MAINTENANCE})

        elif st == ScenarioType.ALTERNATIVE_VESSEL:
            if scenario.alternative_vessel is None:
                raise ValueError("ALTERNATIVE_VESSEL requires 'alternative_vessel'.")
            vessel = scenario.alternative_vessel

        elif st == ScenarioType.ALTERNATIVE_ROUTE:
            if scenario.alternative_route is None:
                raise ValueError("ALTERNATIVE_ROUTE requires 'alternative_route'.")
            route = scenario.alternative_route

        else:  # pragma: no cover - defensive, all enum members handled above
            raise ValueError(f"Unsupported scenario type: {st}")

        return vessel, cargo, route, cost_input, risk_input

    # ------------------------------------------------------------------
    # Snapshot + diff
    # ------------------------------------------------------------------

    @staticmethod
    def _snapshot(voyage_result, cost: VoyageCostBreakdown, risk: RiskAssessmentResult) -> ScenarioSnapshot:
        return ScenarioSnapshot(
            feasible=voyage_result.feasible,
            total_cost=cost.total_cost,
            currency=cost.currency,
            cost_per_mt=cost.cost_per_mt,
            deadline_buffer_days=voyage_result.deadline_buffer_days,
            overall_risk_score=risk.overall_risk_score,
            risk_category=risk.risk_category,
        )

    @staticmethod
    def _diff_snapshots(baseline: ScenarioSnapshot, scenario: ScenarioSnapshot) -> list[ScenarioMetricDiff]:
        metrics = [
            ("total_cost", baseline.total_cost, scenario.total_cost),
            ("cost_per_mt", baseline.cost_per_mt, scenario.cost_per_mt),
            ("deadline_buffer_days", baseline.deadline_buffer_days, scenario.deadline_buffer_days),
            ("overall_risk_score", baseline.overall_risk_score, scenario.overall_risk_score),
        ]
        diffs = []
        for name, b, s in metrics:
            abs_diff = s - b
            pct_diff = None if b == 0 else (abs_diff / abs(b)) * 100.0
            diffs.append(
                ScenarioMetricDiff(
                    metric=name, baseline_value=b, scenario_value=s,
                    absolute_difference=abs_diff, percentage_difference=pct_diff,
                )
            )
        return diffs

    # ------------------------------------------------------------------
    # Recommendation-change check (optional fleet context)
    # ------------------------------------------------------------------

    def _check_recommendation_change(
        self,
        baseline_voyage, baseline_cost, baseline_risk,
        scenario_voyage, scenario_cost, scenario_risk,
        other_voyage_results, other_cost_results, other_risk_results,
        cargo: Cargo,
        ranking_weights: Optional[RankingWeights],
    ) -> tuple[bool, str, str]:
        baseline_ranked = self._ranking.rank(
            [baseline_voyage] + list(other_voyage_results),
            [baseline_cost] + list(other_cost_results),
            [baseline_risk] + list(other_risk_results),
            cargo,
            weights=ranking_weights,
        )
        scenario_ranked = self._ranking.rank(
            [scenario_voyage] + list(other_voyage_results),
            [scenario_cost] + list(other_cost_results),
            [scenario_risk] + list(other_risk_results),
            cargo,
            weights=ranking_weights,
        )
        baseline_feasible = self._ranking.feasible(baseline_ranked)
        scenario_feasible = self._ranking.feasible(scenario_ranked)

        baseline_top = baseline_feasible[0].vessel_id if baseline_feasible else None
        scenario_top = scenario_feasible[0].vessel_id if scenario_feasible else None
        return (baseline_top != scenario_top), baseline_top, scenario_top

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    @staticmethod
    def _build_reasons(
        scenario: ScenarioChange,
        diffs: list[ScenarioMetricDiff],
        baseline: ScenarioSnapshot,
        scenario_snapshot: ScenarioSnapshot,
    ) -> list[str]:
        reasons = [f"Scenario: {scenario.scenario_type.value.replace('_', ' ')}."]
        for d in diffs:
            pct = f"{d.percentage_difference:+.1f}%" if d.percentage_difference is not None else "n/a"
            reasons.append(
                f"{d.metric}: {d.baseline_value:,.2f} -> {d.scenario_value:,.2f} "
                f"({d.absolute_difference:+,.2f}, {pct})."
            )
        if baseline.feasible != scenario_snapshot.feasible:
            reasons.append(
                f"Feasibility changed: {baseline.feasible} -> {scenario_snapshot.feasible}."
            )
        return reasons
