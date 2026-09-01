"""
End-to-End Test (Phase 14).

The canonical scenario specified by the master prompt:

    Cargo:       75,000 MT iron ore
    Origin:      Shanghai
    Destination: Paradip
    Deadline:    15 October 2026

Runs the complete pipeline — matching -> feasibility -> economics ->
risk -> ranking -> decision -> final orchestration -> explainability —
and verifies every required property end to end:

    - infeasible vessels are excluded
    - ETA exists
    - cost exists
    - risk exists
    - ranking exists
    - decision exists
    - explanation exists
    - the result is deterministic
"""

from __future__ import annotations

import pytest

from optimization_engine.data.mock.fixtures import (
    MOCK_VESSELS,
    PARADIP,
    ROUTE_LOOKUP,
    SAMPLE_CARGO,
    SAMPLE_COST_INPUT,
    SHANGHAI,
)
from optimization_engine.decision.engine import DecisionEngine
from optimization_engine.decision.models import DecisionAction
from optimization_engine.economics.engine import VoyageEconomicsEngine
from optimization_engine.explainability.engine import ExplainabilityEngine
from optimization_engine.matching.engine import MatchingEngine
from optimization_engine.optimization.engine import FinalRecommendationEngine
from optimization_engine.ranking.engine import RankingEngine
from optimization_engine.risk.engine import RiskEngine
from optimization_engine.voyage.engine import VoyageFeasibilityEngine


@pytest.fixture(scope="module")
def route():
    return ROUTE_LOOKUP["CNSHA-INPRT"]


class TestCanonicalScenarioAssumptions:
    """Confirm the fixture data actually matches the required scenario."""

    def test_cargo_matches_spec(self) -> None:
        assert SAMPLE_CARGO.quantity_mt == 75_000.0
        assert SAMPLE_CARGO.cargo_type == "iron_ore"
        assert SAMPLE_CARGO.origin_port == "CNSHA"
        assert SAMPLE_CARGO.destination_port == "INPRT"
        assert str(SAMPLE_CARGO.required_arrival_date) == "2026-10-15"

    def test_route_matches_spec(self, route) -> None:
        assert route.origin_port_id == "CNSHA"
        assert route.destination_port_id == "INPRT"


class TestFullPipelineStepByStep:
    """Run each phase explicitly and verify its contract, mirroring how a
    real caller (or the FinalRecommendationEngine internally) would."""

    def test_matching_excludes_infeasible_vessels(self, route) -> None:
        matching_engine = MatchingEngine()
        match_results = matching_engine.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP)
        feasible = matching_engine.feasible(match_results)
        rejected = matching_engine.rejected(match_results)

        assert len(match_results) == len(MOCK_VESSELS)
        assert len(feasible) > 0
        assert len(feasible) + len(rejected) == len(match_results)
        for mr in rejected:
            assert len(mr.rejection_reasons) > 0
        for mr in feasible:
            assert mr.feasible is True

    def test_eta_exists_for_every_feasible_vessel(self, route) -> None:
        matching_engine = MatchingEngine()
        feasible_matches = matching_engine.feasible(
            matching_engine.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP)
        )
        voyage_engine = VoyageFeasibilityEngine()
        voyage_results = voyage_engine.evaluate_all(feasible_matches, route, SAMPLE_CARGO)

        for vr in voyage_results:
            assert vr.estimated_arrival is not None
            assert vr.deadline_buffer_days is not None

        voyage_feasible = [vr for vr in voyage_results if vr.feasible]
        assert len(voyage_feasible) > 0

    def test_cost_exists_for_every_feasible_voyage(self, route) -> None:
        matching_engine = MatchingEngine()
        feasible_matches = matching_engine.feasible(
            matching_engine.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP)
        )
        voyage_engine = VoyageFeasibilityEngine()
        voyage_feasible = [
            vr for vr in voyage_engine.evaluate_all(feasible_matches, route, SAMPLE_CARGO) if vr.feasible
        ]
        economics_engine = VoyageEconomicsEngine()
        cost_results = [economics_engine.calculate(vr, SAMPLE_CARGO, SAMPLE_COST_INPUT) for vr in voyage_feasible]

        assert len(cost_results) == len(voyage_feasible)
        for cost in cost_results:
            assert cost.total_cost > 0
            assert cost.cost_per_mt > 0

    def test_risk_exists_for_every_feasible_voyage(self, route) -> None:
        matching_engine = MatchingEngine()
        feasible_matches = matching_engine.feasible(
            matching_engine.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP)
        )
        voyage_engine = VoyageFeasibilityEngine()
        voyage_feasible = [
            vr for vr in voyage_engine.evaluate_all(feasible_matches, route, SAMPLE_CARGO) if vr.feasible
        ]
        risk_results = RiskEngine().assess_all(voyage_feasible, SAMPLE_CARGO)

        assert len(risk_results) == len(voyage_feasible)
        for risk in risk_results:
            assert 0.0 <= risk.overall_risk_score <= 100.0
            assert len(risk.factor_scores) == 10

    def test_ranking_exists_and_excludes_infeasible(self, route) -> None:
        matching_engine = MatchingEngine()
        match_results = matching_engine.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP)
        feasible_matches = matching_engine.feasible(match_results)
        voyage_engine = VoyageFeasibilityEngine()
        voyage_results = voyage_engine.evaluate_all(feasible_matches, route, SAMPLE_CARGO)
        voyage_feasible = [vr for vr in voyage_results if vr.feasible]

        economics_engine = VoyageEconomicsEngine()
        cost_results = [economics_engine.calculate(vr, SAMPLE_CARGO, SAMPLE_COST_INPUT) for vr in voyage_feasible]
        risk_results = RiskEngine().assess_all(voyage_feasible, SAMPLE_CARGO)

        ranking_engine = RankingEngine()
        ranked = ranking_engine.rank(voyage_results, cost_results, risk_results, SAMPLE_CARGO)
        ranked_feasible = ranking_engine.feasible(ranked)
        ranked_excluded = ranking_engine.excluded(ranked)

        assert len(ranked_feasible) == len(voyage_feasible)
        assert all(rv.rank is not None for rv in ranked_feasible)
        assert all(rv.rank is None for rv in ranked_excluded)
        assert [rv.rank for rv in ranked_feasible] == list(range(1, len(ranked_feasible) + 1))

    def test_decision_exists(self, route) -> None:
        matching_engine = MatchingEngine()
        feasible_matches = matching_engine.feasible(
            matching_engine.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP)
        )
        voyage_engine = VoyageFeasibilityEngine()
        voyage_results = voyage_engine.evaluate_all(feasible_matches, route, SAMPLE_CARGO)
        voyage_feasible = [vr for vr in voyage_results if vr.feasible]
        economics_engine = VoyageEconomicsEngine()
        cost_results = [economics_engine.calculate(vr, SAMPLE_CARGO, SAMPLE_COST_INPUT) for vr in voyage_feasible]
        risk_results = RiskEngine().assess_all(voyage_feasible, SAMPLE_CARGO)
        ranked = RankingEngine().rank(voyage_results, cost_results, risk_results, SAMPLE_CARGO)

        decision = DecisionEngine().decide(ranked, SAMPLE_CARGO, current_route=route)
        assert decision.recommended_action != DecisionAction.NO_FEASIBLE_OPTION
        assert decision.selected_vessel_id is not None
        assert len(decision.alternatives) > 0


class TestFullPipelineViaFinalRecommendationEngine:
    """The convenience one-call path must produce the same guarantees."""

    def test_final_recommendation_has_everything(self, route) -> None:
        engine = FinalRecommendationEngine()
        rec = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, route, SAMPLE_COST_INPUT)

        assert rec.feasible is True
        assert rec.selected_vessel_id is not None
        assert rec.selected_route is not None
        assert rec.estimated_arrival is not None  # ETA exists
        assert rec.expected_total_cost is not None and rec.expected_total_cost > 0  # cost exists
        assert rec.risk_score is not None  # risk exists
        assert len(rec.ranked_vessels_on_selected_route) > 0  # ranking exists
        assert rec.recommended_action is not None  # decision exists
        assert len(rec.explanation) > 0  # explanation exists
        assert rec.emissions is not None  # optional emissions computed by default

    def test_explanation_via_explainability_engine(self, route) -> None:
        engine = FinalRecommendationEngine()
        rec = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, route, SAMPLE_COST_INPUT)
        report = ExplainabilityEngine().explain(rec)

        assert report.summary != ""
        assert len(report.why_this_vessel) > 0
        assert len(report.why_this_action) > 0
        assert rec.selected_vessel_name in report.summary

    def test_deterministic_end_to_end(self, route) -> None:
        engine = FinalRecommendationEngine()
        rec1 = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, route, SAMPLE_COST_INPUT)
        rec2 = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, route, SAMPLE_COST_INPUT)

        assert rec1.selected_vessel_id == rec2.selected_vessel_id
        assert rec1.recommended_action == rec2.recommended_action
        assert rec1.expected_total_cost == rec2.expected_total_cost
        assert rec1.risk_score == rec2.risk_score
        assert rec1.deadline_buffer_days == rec2.deadline_buffer_days

    def test_never_selects_infeasible_vessel(self, route) -> None:
        """Cross-check: the selected vessel must be among the feasible set
        independently computed via Phase 1+2, not just trusted blindly."""
        matching_engine = MatchingEngine()
        feasible_matches = matching_engine.feasible(
            matching_engine.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP)
        )
        feasible_vessel_ids = {m.vessel.vessel_id for m in feasible_matches}

        engine = FinalRecommendationEngine()
        rec = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, route, SAMPLE_COST_INPUT)

        assert rec.selected_vessel_id in feasible_vessel_ids
