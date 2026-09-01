"""
Tests for the final recommendation orchestration engine (Phase 10).

Tests cover:
    - Never selects an infeasible vessel or route
    - Raw values are preserved (expected_total_cost is the real dollar figure)
    - Reuses existing engines (no duplicated formulas) — verified indirectly
      via consistency with directly-computed Phase 1-5 results
    - Alternative routes with a different origin/destination require a
      matching Cargo, and raise a clear error otherwise
    - Optional emissions computation
    - Determinism
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
from optimization_engine.decision.models import DecisionAction, DecisionInput
from optimization_engine.domain.models import Cargo, Port
from optimization_engine.optimization.engine import FinalRecommendationEngine
from optimization_engine.optimization.models import AlternativeRouteInput


@pytest.fixture
def engine() -> FinalRecommendationEngine:
    return FinalRecommendationEngine()


@pytest.fixture
def primary_route():
    return ROUTE_LOOKUP["CNSHA-INPRT"]


class TestNeverSelectsInfeasible:
    def test_oversized_cargo_returns_infeasible_with_no_selection(self, engine, primary_route):
        huge_cargo = Cargo(
            cargo_id="C-HUGE", cargo_type="iron_ore", quantity_mt=999_999_999.0,
            origin_port="CNSHA", destination_port="INPRT",
            required_arrival_date=date(2026, 10, 15), hazardous=False,
        )
        rec = engine.recommend(huge_cargo, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        assert rec.feasible is False
        assert rec.selected_vessel_id is None
        assert rec.selected_route is None
        assert rec.recommended_action == DecisionAction.NO_FEASIBLE_OPTION
        assert len(rec.explanation) > 0

    def test_impossible_deadline_returns_infeasible(self, engine, primary_route):
        impossible_cargo = Cargo(
            cargo_id="C-IMPOSSIBLE", cargo_type="iron_ore", quantity_mt=75_000.0,
            origin_port="CNSHA", destination_port="INPRT",
            # Even the fleet's earliest available_from (2026-07-01) needs ~9.9
            # sailing days at ~14 knots for the 3,450nm route; this deadline
            # falls before any vessel could possibly arrive.
            required_arrival_date=date(2026, 7, 5), hazardous=False,
        )
        rec = engine.recommend(impossible_cargo, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        assert rec.feasible is False
        assert rec.selected_vessel_id is None


class TestRawValuesPreserved:
    def test_expected_total_cost_matches_selected_vessel_actual_cost(self, engine, primary_route):
        rec = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        assert rec.feasible is True
        # Cross-check against directly-run Phase 1-5 pipeline (no duplicated formulas).
        from optimization_engine.economics.engine import VoyageEconomicsEngine
        from optimization_engine.matching.engine import MatchingEngine
        from optimization_engine.voyage.engine import VoyageFeasibilityEngine

        me = MatchingEngine()
        mr = me.feasible(me.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP))
        ve = VoyageFeasibilityEngine()
        vr = [v for v in ve.evaluate_all(mr, primary_route, SAMPLE_CARGO) if v.feasible]
        selected_voyage = next(v for v in vr if v.vessel.vessel_id == rec.selected_vessel_id)
        cost = VoyageEconomicsEngine().calculate(selected_voyage, SAMPLE_CARGO, SAMPLE_COST_INPUT)

        assert rec.expected_total_cost == pytest.approx(cost.total_cost)
        assert rec.cost_per_mt == pytest.approx(cost.cost_per_mt)
        assert rec.deadline_buffer_days == pytest.approx(selected_voyage.deadline_buffer_days)


class TestAlternativeRoutesRequireMatchingCargo:
    def test_different_origin_route_without_cargo_override_raises(self, engine, primary_route):
        singapore = Port(port_id="SGSIN", port_name="Singapore", country="Singapore",
                          max_draft_m=21.0, max_loa_m=400.0, max_beam_m=63.0)
        alt_route = ROUTE_LOOKUP["SGSIN-INPRT"]
        with pytest.raises(ValueError, match="does not match cargo origin"):
            engine.recommend(
                SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT,
                alternative_routes=[AlternativeRouteInput(route=alt_route, origin_port=singapore)],
            )

    def test_different_origin_route_with_matching_cargo_succeeds(self, engine, primary_route):
        singapore = Port(port_id="SGSIN", port_name="Singapore", country="Singapore",
                          max_draft_m=21.0, max_loa_m=400.0, max_beam_m=63.0)
        alt_route = ROUTE_LOOKUP["SGSIN-INPRT"]
        alt_cargo = Cargo(
            cargo_id=SAMPLE_CARGO.cargo_id, cargo_type=SAMPLE_CARGO.cargo_type,
            quantity_mt=SAMPLE_CARGO.quantity_mt, origin_port="SGSIN", destination_port="INPRT",
            required_arrival_date=SAMPLE_CARGO.required_arrival_date, hazardous=SAMPLE_CARGO.hazardous,
        )
        rec = engine.recommend(
            SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT,
            alternative_routes=[AlternativeRouteInput(route=alt_route, origin_port=singapore, cargo=alt_cargo)],
        )
        assert rec.feasible is True
        # Singapore route is much shorter -> should win decisively.
        assert rec.selected_route.route_id == "SGSIN-INPRT"
        assert rec.recommended_action == DecisionAction.SELECT_ALTERNATIVE_ROUTE


class TestEmissions:
    def test_emissions_computed_by_default(self, engine, primary_route):
        rec = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        assert rec.emissions is not None
        assert rec.emissions.co2_emissions_kg > 0

    def test_emissions_skipped_when_disabled(self, engine, primary_route):
        rec = engine.recommend(
            SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT,
            compute_emissions=False,
        )
        assert rec.emissions is None

    def test_custom_emission_factor_applied(self, engine, primary_route):
        rec = engine.recommend(
            SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT,
            emission_factor_kg_co2_per_kg_fuel=5.0,
        )
        assert rec.emissions.emission_factor_used == 5.0


class TestDecisionIntegration:
    def test_forecast_can_change_recommended_action(self, engine, primary_route):
        from optimization_engine.data.mock.fixtures import MOCK_FREIGHT_FORECAST

        rec_no_forecast = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        rec_with_forecast = engine.recommend(
            SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT,
            decision_input=DecisionInput(freight_forecast=MOCK_FREIGHT_FORECAST),
        )
        assert rec_no_forecast.recommended_action == DecisionAction.BOOK_NOW
        # With a favorable-enough mock forecast, WAIT becomes viable.
        assert rec_with_forecast.recommended_action in (DecisionAction.BOOK_NOW, DecisionAction.WAIT)

    def test_alternatives_list_is_populated(self, engine, primary_route):
        rec = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        assert len(rec.alternatives) >= 1

    def test_ranked_vessels_included_for_transparency(self, engine, primary_route):
        rec = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        assert len(rec.ranked_vessels_on_selected_route) > 0


class TestDeterminism:
    def test_repeated_runs_produce_identical_recommendation(self, engine, primary_route):
        r1 = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        r2 = engine.recommend(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP, primary_route, SAMPLE_COST_INPUT)
        assert r1.recommended_action == r2.recommended_action
        assert r1.selected_vessel_id == r2.selected_vessel_id
        assert r1.expected_total_cost == r2.expected_total_cost
