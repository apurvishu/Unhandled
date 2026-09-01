"""
Final Recommendation Engine (Phase 10).

Orchestrates Cargo -> Matching -> Voyage Feasibility -> Economics ->
Risk -> Ranking -> Decision -> (optional) Emissions into one
deterministic ``FinalRecommendation``. Every calculation is delegated
to the already-tested Phase 1-9 engines; nothing is duplicated here.

WHY THIS IS NOT CALLED "OptimizationEngine": there is no defined
mathematical optimization problem (no decision variables, objective
function, or constraint set) — see the project's rule that OR-Tools
(or any solver) must not be introduced without one. This class name
deliberately avoids implying a solver; it is a deterministic
orchestration/decision layer.
"""

from __future__ import annotations

from typing import Optional

from optimization_engine.decision.engine import DecisionEngine
from optimization_engine.decision.models import DecisionAction, DecisionInput
from optimization_engine.domain.models import Cargo, Port, Route, Vessel
from optimization_engine.economics.engine import VoyageEconomicsEngine
from optimization_engine.economics.models import VoyageCostInput
from optimization_engine.emissions.engine import EmissionsEngine
from optimization_engine.emissions.models import EmissionsInput
from optimization_engine.matching.engine import MatchingEngine
from optimization_engine.multiroute.models import RouteCandidate
from optimization_engine.optimization.models import AlternativeRouteInput, FinalRecommendation
from optimization_engine.ranking.engine import RankingEngine
from optimization_engine.ranking.models import RankingWeights
from optimization_engine.risk.engine import RiskEngine
from optimization_engine.risk.models import RiskFactorInput, RiskWeights
from optimization_engine.voyage.engine import VoyageFeasibilityEngine

_BASELINE_ASSUMPTIONS: list[str] = [
    "This layer performs no mathematical optimization (no OR-Tools, no defined decision "
    "variables/objective/constraints) — it deterministically orchestrates Phases 1-9.",
    "Never selects an infeasible vessel or route: the decision layer only ever picks from "
    "Phase 5's feasible() shortlist, on the primary route or an explicitly supplied alternative.",
    "Alternative routes must match their own cargo's origin/destination exactly (Phase 2's "
    "existing validation, preserved unweakened) — supply AlternativeRouteInput.cargo whenever "
    "the alternative route's origin or destination differs from the primary cargo's.",
    "Emissions are optional and, when computed, use fuel already consumed for the selected "
    "voyage (Phase 3) — this layer does not model alternative fuels or engine efficiency.",
]


class FinalRecommendationEngine:
    """Runs the complete Phase 1-9 pipeline and returns one FinalRecommendation.

    Usage::

        engine = FinalRecommendationEngine()
        recommendation = engine.recommend(
            cargo, vessels, origin_port, destination_port, primary_route, cost_input,
        )
    """

    def __init__(self) -> None:
        self._matching = MatchingEngine()
        self._voyage = VoyageFeasibilityEngine()
        self._economics = VoyageEconomicsEngine()
        self._risk = RiskEngine()
        self._ranking = RankingEngine()
        self._decision = DecisionEngine()
        self._emissions = EmissionsEngine()

    def recommend(
        self,
        cargo: Cargo,
        vessels: list[Vessel],
        origin_port: Port,
        destination_port: Port,
        primary_route: Route,
        cost_input: VoyageCostInput,
        *,
        alternative_routes: Optional[list[AlternativeRouteInput]] = None,
        risk_input: Optional[RiskFactorInput] = None,
        risk_weights: Optional[RiskWeights] = None,
        ranking_weights: Optional[RankingWeights] = None,
        decision_input: Optional[DecisionInput] = None,
        compute_emissions: bool = True,
        emission_factor_kg_co2_per_kg_fuel: Optional[float] = None,
    ) -> FinalRecommendation:
        """Run the full pipeline and produce one explainable recommendation.

        Args:
            cargo: Cargo requirement.
            vessels: Candidate vessels to evaluate on the primary route.
            origin_port, destination_port: Primary route's ports.
            primary_route: The main route to evaluate.
            cost_input: Configurable voyage cost rates.
            alternative_routes: Optional list of alternative routes to
                compare against (Phase 8 integration).
            risk_input, risk_weights: Optional Phase 4 configuration.
            ranking_weights: Optional Phase 5 configuration.
            decision_input: Optional Phase 6 policy configuration
                (including an optional external freight forecast).
            compute_emissions: Whether to compute Phase 9 emissions
                for the selected voyage.
            emission_factor_kg_co2_per_kg_fuel: Optional override for
                the emission factor used, if computed.

        Returns:
            A ``FinalRecommendation``. If no feasible vessel/route
            combination exists, ``feasible=False`` and no vessel or
            route is ever selected.
        """
        primary_data = self._build_route_data(
            cargo, vessels, origin_port, destination_port, primary_route,
            cost_input, risk_input, risk_weights, ranking_weights,
        )

        route_data_by_id = {primary_route.route_id: primary_data}
        alt_candidates: list[RouteCandidate] = []
        for alt in alternative_routes or []:
            alt_origin = alt.origin_port if alt.origin_port is not None else origin_port
            alt_destination = alt.destination_port if alt.destination_port is not None else destination_port
            alt_cargo = alt.cargo if alt.cargo is not None else cargo
            alt_data = self._build_route_data(
                alt_cargo, vessels, alt_origin, alt_destination, alt.route,
                cost_input, risk_input, risk_weights, ranking_weights,
            )
            route_data_by_id[alt.route.route_id] = alt_data
            alt_candidates.append(
                RouteCandidate(route=alt.route, ranked_vessels=alt_data["ranked_vessels"], risk_results=alt_data["risk_results"])
            )

        decision = self._decision.decide(
            primary_data["ranked_vessels"],
            cargo,
            current_route=primary_route,
            decision_input=decision_input,
            alternative_routes=alt_candidates or None,
        )

        if decision.recommended_action == DecisionAction.NO_FEASIBLE_OPTION:
            return FinalRecommendation(
                cargo_id=cargo.cargo_id,
                feasible=False,
                recommended_action=decision.recommended_action,
                alternatives=decision.alternatives,
                ranked_vessels_on_selected_route=primary_data["ranked_vessels"],
                explanation=decision.reasons,
                assumptions=list(_BASELINE_ASSUMPTIONS) + decision.assumptions,
            )

        selected_route_id = decision.selected_route.route_id if decision.selected_route else primary_route.route_id
        selected_data = route_data_by_id[selected_route_id]

        voyage_result = next(
            v for v in selected_data["voyage_results"] if v.vessel.vessel_id == decision.selected_vessel_id
        )
        cost_result = next(
            c for c in selected_data["cost_results"] if c.vessel_id == decision.selected_vessel_id
        )

        emissions_result = None
        if compute_emissions:
            emissions_kwargs = dict(
                fuel_consumed_mt=cost_result.fuel_consumed_mt,
                distance_nm=voyage_result.route.distance_nm,
                cargo_quantity_mt=cargo.quantity_mt,
            )
            if emission_factor_kg_co2_per_kg_fuel is not None:
                emissions_kwargs["emission_factor_kg_co2_per_kg_fuel"] = emission_factor_kg_co2_per_kg_fuel
            emissions_result = self._emissions.calculate(EmissionsInput(**emissions_kwargs))

        explanation = list(decision.reasons)
        if emissions_result is not None:
            explanation.append(
                f"Estimated emissions for this voyage: {emissions_result.co2_emissions_mt:,.2f} MT CO2 "
                f"({emissions_result.co2_per_tonne_kg:.2f} kg/MT cargo)."
            )

        return FinalRecommendation(
            cargo_id=cargo.cargo_id,
            feasible=True,
            recommended_action=decision.recommended_action,
            selected_vessel_id=decision.selected_vessel_id,
            selected_vessel_name=decision.selected_vessel_name,
            selected_route=decision.selected_route or primary_route,
            estimated_arrival=voyage_result.estimated_arrival,
            deadline_buffer_days=voyage_result.deadline_buffer_days,
            expected_total_cost=decision.expected_total_cost,
            cost_per_mt=cost_result.cost_per_mt,
            risk_score=decision.risk_score,
            risk_category=decision.risk_category,
            emissions=emissions_result,
            alternatives=decision.alternatives,
            ranked_vessels_on_selected_route=selected_data["ranked_vessels"],
            expected_savings=decision.expected_savings,
            explanation=explanation,
            assumptions=list(_BASELINE_ASSUMPTIONS) + decision.assumptions,
        )

    # ------------------------------------------------------------------
    # Internal: run Phases 1-5 for one route
    # ------------------------------------------------------------------

    def _build_route_data(
        self,
        cargo: Cargo,
        vessels: list[Vessel],
        origin_port: Port,
        destination_port: Port,
        route: Route,
        cost_input: VoyageCostInput,
        risk_input: Optional[RiskFactorInput],
        risk_weights: Optional[RiskWeights],
        ranking_weights: Optional[RankingWeights],
    ) -> dict:
        match_results = self._matching.match_vessels(cargo, vessels, origin_port, destination_port)
        feasible_matches = self._matching.feasible(match_results)

        voyage_results = self._voyage.evaluate_all(feasible_matches, route, cargo)
        voyage_feasible = [v for v in voyage_results if v.feasible]

        cost_results = [self._economics.calculate(v, cargo, cost_input) for v in voyage_feasible]
        risk_inputs_by_vessel_id = (
            {v.vessel.vessel_id: risk_input for v in voyage_feasible} if risk_input is not None else None
        )
        risk_results = self._risk.assess_all(
            voyage_feasible, cargo, risk_inputs_by_vessel_id=risk_inputs_by_vessel_id, weights=risk_weights
        )

        ranked_vessels = self._ranking.rank(voyage_results, cost_results, risk_results, cargo, weights=ranking_weights)

        return {
            "voyage_results": voyage_results,
            "cost_results": cost_results,
            "risk_results": risk_results,
            "ranked_vessels": ranked_vessels,
        }
