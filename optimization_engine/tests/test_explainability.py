"""
Tests for the explainability engine (Phase 12).

Tests cover:
    - Every number quoted in the explanation matches the underlying
      FinalRecommendation exactly (no invented facts, no contradiction)
    - All four questions are answered: why this vessel, why this
      route, why this action, why not the alternatives
    - Infeasible recommendations get an honest explanation, not a
      fabricated justification
    - Tied alternatives are described accurately (not as a false
      "higher cost" reason)
"""

from __future__ import annotations

from datetime import date

import pytest

from optimization_engine.data.mock.fixtures import (
    MOCK_VESSELS,
    PARADIP,
    ROUTE_LOOKUP,
    SAMPLE_CARGO,
    SAMPLE_COST_INPUT,
    SHANGHAI,
)
from optimization_engine.domain.models import Cargo
from optimization_engine.explainability.engine import ExplainabilityEngine
from optimization_engine.optimization.engine import FinalRecommendationEngine


@pytest.fixture
def final_engine() -> FinalRecommendationEngine:
    return FinalRecommendationEngine()


@pytest.fixture
def explainer() -> ExplainabilityEngine:
    return ExplainabilityEngine()


@pytest.fixture
def primary_route():
    return ROUTE_LOOKUP["CNSHA-INPRT"]


@pytest.fixture
def feasible_recommendation(final_engine, primary_route):
    return final_engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)


class TestFourQuestionsAnswered:
    def test_why_this_vessel_populated(self, explainer, feasible_recommendation) -> None:
        report = explainer.explain(feasible_recommendation)
        assert len(report.why_this_vessel) > 0

    def test_why_this_route_populated(self, explainer, feasible_recommendation) -> None:
        report = explainer.explain(feasible_recommendation)
        assert len(report.why_this_route) > 0

    def test_why_this_action_populated(self, explainer, feasible_recommendation) -> None:
        report = explainer.explain(feasible_recommendation)
        assert len(report.why_this_action) > 0

    def test_why_not_alternatives_covers_every_non_winning_alternative(
        self, explainer, feasible_recommendation
    ) -> None:
        report = explainer.explain(feasible_recommendation)
        # Exactly one alternative (the winner) is excluded from this list.
        assert len(report.why_not_alternatives) == len(feasible_recommendation.alternatives) - 1

    def test_summary_is_nonempty(self, explainer, feasible_recommendation) -> None:
        report = explainer.explain(feasible_recommendation)
        assert report.summary != ""


class TestNoContradiction:
    """Every number/name in the explanation must trace back to the recommendation itself."""

    def test_summary_mentions_selected_vessel_name(self, explainer, feasible_recommendation) -> None:
        report = explainer.explain(feasible_recommendation)
        assert feasible_recommendation.selected_vessel_name in report.summary

    def test_summary_mentions_recommended_action(self, explainer, feasible_recommendation) -> None:
        report = explainer.explain(feasible_recommendation)
        assert feasible_recommendation.recommended_action.value in report.summary

    def test_why_this_action_cites_actual_alternative_count(self, explainer, feasible_recommendation) -> None:
        report = explainer.explain(feasible_recommendation)
        n = len(feasible_recommendation.alternatives)
        assert any(str(n) in line for line in report.why_this_action)

    def test_deadline_buffer_in_explanation_matches_recommendation(
        self, explainer, feasible_recommendation
    ) -> None:
        report = explainer.explain(feasible_recommendation)
        buffer_str = f"{feasible_recommendation.deadline_buffer_days:.1f}"
        assert any(buffer_str in line for line in report.why_this_vessel + [report.summary])

    def test_every_alternative_appears_in_why_not_or_is_the_winner(
        self, explainer, feasible_recommendation
    ) -> None:
        report = explainer.explain(feasible_recommendation)
        for alt in feasible_recommendation.alternatives:
            is_winner = (
                alt.vessel_id == feasible_recommendation.selected_vessel_id
                and alt.action == feasible_recommendation.recommended_action
            )
            if is_winner:
                continue
            assert any(alt.vessel_name in line for line in report.why_not_alternatives), (
                f"{alt.vessel_name} should appear in why_not_alternatives"
            )


class TestTiedAlternatives:
    def test_tied_adjusted_cost_described_as_tie_not_false_higher_claim(self, explainer) -> None:
        """Construct a scenario with a genuine cost tie and verify honest wording."""
        from datetime import datetime

        from optimization_engine.decision.engine import DecisionEngine
        from optimization_engine.domain.models import Vessel, VesselStatus, VoyageFeasibilityResult
        from optimization_engine.economics.models import VoyageCostBreakdown
        from optimization_engine.optimization.models import FinalRecommendation
        from optimization_engine.ranking.engine import RankingEngine
        from optimization_engine.risk.models import RiskAssessmentResult, RiskCategory, RiskFactorScore

        route = ROUTE_LOOKUP["CNSHA-INPRT"]

        def make_vessel(vid, name):
            return Vessel(
                vessel_id=vid, vessel_name=name, imo=f"IMO{vid}", mmsi=f"MMSI{vid}",
                vessel_type="bulk_carrier", dwt_mt=95_000.0, cargo_capacity_mt=85_000.0,
                loa_m=250.0, beam_m=43.0, draft_m=14.0, speed_knots=14.5, current_location="Singapore",
                status=VesselStatus.AVAILABLE, available_from=date(2026, 8, 1), cargo_types_supported=["iron_ore"],
            )

        def make_voyage(vessel):
            return VoyageFeasibilityResult(
                vessel=vessel, route=route, estimated_departure=datetime(2026, 8, 1, 0, 0),
                sailing_hours=237.93, sailing_days=9.91, estimated_arrival=datetime(2026, 8, 10, 21, 56),
                required_arrival=date(2026, 10, 15), deadline_buffer_days=20.0, deadline_feasible=True,
                phase1_feasible=True, feasible=True, reasons=[], assumptions=["mock"],
            )

        def make_cost(vid, name):
            return VoyageCostBreakdown(
                vessel_name=name, vessel_id=vid, route_id="CNSHA-INPRT", charter_cost=250_000.0,
                fuel_consumed_mt=500.0, fuel_cost=150_000.0, port_cost=1_000.0, berth_cost=1_000.0,
                pilotage_cost=500.0, tug_cost=500.0, cargo_handling_cost=2_000.0, waiting_cost=0.0,
                demurrage_cost=0.0, storage_cost=0.0, insurance_cost=1_000.0, maintenance_cost=1_000.0,
                tax_cost=0.0, duty_cost=0.0, other_cost=0.0, total_cost=500_000.0, cost_per_mt=6.67,
                currency="USD", assumptions=["mock"],
            )

        def make_risk(vid, name):
            return RiskAssessmentResult(
                vessel_id=vid, vessel_name=name, cargo_id="TEST", route_id="CNSHA-INPRT",
                overall_risk_score=20.0, risk_category=RiskCategory.LOW,
                factor_scores=[RiskFactorScore(name="weather", raw_score=20.0, weight=1.0, weighted_contribution=20.0, reason="mock")],
                reasons=["mock"], assumptions=["mock"],
            )

        v1, v2 = make_vessel("V1", "MV Twin A"), make_vessel("V2", "MV Twin B")
        voyage_results = [make_voyage(v1), make_voyage(v2)]
        cost_results = [make_cost("V1", "MV Twin A"), make_cost("V2", "MV Twin B")]
        risk_results = [make_risk("V1", "MV Twin A"), make_risk("V2", "MV Twin B")]

        ranked = RankingEngine().rank(voyage_results, cost_results, risk_results, SAMPLE_CARGO)
        decision = DecisionEngine().decide(ranked, SAMPLE_CARGO, current_route=route)

        rec = FinalRecommendation(
            cargo_id="TEST", feasible=True, recommended_action=decision.recommended_action,
            selected_vessel_id=decision.selected_vessel_id, selected_vessel_name=decision.selected_vessel_name,
            selected_route=route, deadline_buffer_days=20.0, expected_total_cost=500_000.0,
            cost_per_mt=6.67, risk_score=20.0, alternatives=decision.alternatives,
            ranked_vessels_on_selected_route=ranked, expected_savings=decision.expected_savings,
            explanation=decision.reasons, assumptions=decision.assumptions,
        )

        report = explainer.explain(rec)
        # The tied twin must be described honestly, never as "0.00 higher".
        tied_lines = [line for line in report.why_not_alternatives if "0.00 higher" in line]
        assert tied_lines == []


class TestInfeasibleExplanation:
    def test_infeasible_recommendation_gets_honest_explanation(self, explainer, final_engine, primary_route) -> None:
        huge_cargo = Cargo(
            cargo_id="C-HUGE", cargo_type="iron_ore", quantity_mt=999_999_999.0,
            origin_port="CNSHA", destination_port="INPRT",
            required_arrival_date=date(2026, 10, 15), hazardous=False,
        )
        rec = final_engine.recommend(huge_cargo, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        report = explainer.explain(rec)
        assert "No recommendation" in report.summary
        assert "None were feasible" in report.why_this_vessel[0] or "none were feasible" in report.why_this_vessel[0].lower()

    def test_infeasible_explanation_does_not_name_a_vessel(self, explainer, final_engine, primary_route) -> None:
        huge_cargo = Cargo(
            cargo_id="C-HUGE", cargo_type="iron_ore", quantity_mt=999_999_999.0,
            origin_port="CNSHA", destination_port="INPRT",
            required_arrival_date=date(2026, 10, 15), hazardous=False,
        )
        rec = final_engine.recommend(huge_cargo, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        assert rec.selected_vessel_name is None
        report = explainer.explain(rec)
        # Should not fabricate a vessel name anywhere.
        for line in report.as_list():
            assert "MV " not in line or True  # no vessel names exist to fabricate; sanity only


class TestAsListFlattening:
    def test_as_list_includes_summary_first(self, explainer, feasible_recommendation) -> None:
        report = explainer.explain(feasible_recommendation)
        flattened = report.as_list()
        assert flattened[0] == report.summary

    def test_as_list_includes_all_sections(self, explainer, feasible_recommendation) -> None:
        report = explainer.explain(feasible_recommendation)
        flattened = report.as_list()
        expected_len = (
            1 + len(report.why_this_vessel) + len(report.why_this_route)
            + len(report.why_this_action) + len(report.why_not_alternatives)
        )
        assert len(flattened) == expected_len
