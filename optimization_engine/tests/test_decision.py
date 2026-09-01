"""
Tests for the charter decision engine (Phase 6).

Tests cover:
    - BOOK_NOW as the default when no forecast is supplied
    - SELECT_ALTERNATIVE_VESSEL when the top-ranked vessel exceeds the
      risk threshold
    - WAIT only when a forecast makes it genuinely worthwhile and
      deadline-safe
    - BOOK_NOW even with a forecast present, when waiting isn't justified
    - NO_FEASIBLE_OPTION when there are no feasible vessels
    - SELECT_ALTERNATIVE_ROUTE when another route is meaningfully better
    - "Compare, don't cascade": all relevant alternatives appear in
      DecisionResult.alternatives, not just the winner
    - Raw values are preserved (expected_total_cost is never replaced
      by adjusted_cost)
    - Determinism
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from optimization_engine.decision.calculations import (
    calculate_adjusted_cost,
    calculate_expected_waiting_cost,
    calculate_net_expected_benefit,
    calculate_predicted_savings_per_mt,
)
from optimization_engine.decision.engine import DecisionEngine
from optimization_engine.decision.models import DecisionAction, DecisionInput, FreightForecastInput
from optimization_engine.domain.models import Cargo, Route, Vessel, VesselStatus, VoyageFeasibilityResult
from optimization_engine.economics.models import VoyageCostBreakdown
from optimization_engine.multiroute.models import RouteCandidate
from optimization_engine.ranking.engine import RankingEngine
from optimization_engine.risk.models import RiskAssessmentResult, RiskCategory, RiskFactorScore


# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def decision_engine() -> DecisionEngine:
    return DecisionEngine()


@pytest.fixture
def ranking_engine() -> RankingEngine:
    return RankingEngine()


@pytest.fixture
def cargo() -> Cargo:
    return Cargo(
        cargo_id="TEST-DEC-001",
        cargo_type="iron_ore",
        quantity_mt=75_000.0,
        origin_port="CNSHA",
        destination_port="INPRT",
        required_arrival_date=date(2026, 10, 15),
        hazardous=False,
    )


@pytest.fixture
def route() -> Route:
    return Route(route_id="R1", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_450.0)


def _make_vessel(vessel_id: str, name: str, capacity_mt: float = 85_000.0) -> Vessel:
    return Vessel(
        vessel_id=vessel_id, vessel_name=name, imo=f"IMO{vessel_id}", mmsi=f"MMSI{vessel_id}",
        vessel_type="bulk_carrier", dwt_mt=capacity_mt + 10_000, cargo_capacity_mt=capacity_mt,
        loa_m=250.0, beam_m=43.0, draft_m=14.0, speed_knots=14.5, current_location="Singapore",
        status=VesselStatus.AVAILABLE, available_from=date(2026, 8, 1),
        cargo_types_supported=["iron_ore"],
    )


def _make_voyage_result(
    vessel: Vessel, route: Route, buffer_days: float = 10.0, feasible: bool = True
) -> VoyageFeasibilityResult:
    return VoyageFeasibilityResult(
        vessel=vessel, route=route,
        estimated_departure=datetime(2026, 8, 1, 0, 0), sailing_hours=237.93, sailing_days=9.91,
        estimated_arrival=datetime(2026, 8, 10, 21, 56), required_arrival=date(2026, 10, 15),
        deadline_buffer_days=buffer_days, deadline_feasible=feasible, phase1_feasible=feasible,
        feasible=feasible, reasons=[] if feasible else ["mock rejection"], assumptions=["mock"],
    )


def _make_cost(vessel_id: str, name: str, total_cost: float, cost_per_mt: float, route_id: str = "R1") -> VoyageCostBreakdown:
    return VoyageCostBreakdown(
        vessel_name=name, vessel_id=vessel_id, route_id=route_id,
        charter_cost=total_cost * 0.5, fuel_consumed_mt=500.0, fuel_cost=total_cost * 0.3,
        port_cost=1_000.0, berth_cost=1_000.0, pilotage_cost=500.0, tug_cost=500.0,
        cargo_handling_cost=2_000.0, waiting_cost=0.0, demurrage_cost=0.0, storage_cost=0.0,
        insurance_cost=1_000.0, maintenance_cost=1_000.0, tax_cost=0.0, duty_cost=0.0, other_cost=0.0,
        total_cost=total_cost, cost_per_mt=cost_per_mt, currency="USD", assumptions=["mock"],
    )


def _make_risk(vessel_id: str, name: str, score: float, category: RiskCategory, route_id: str = "R1") -> RiskAssessmentResult:
    return RiskAssessmentResult(
        vessel_id=vessel_id, vessel_name=name, cargo_id="TEST-DEC-001", route_id=route_id,
        overall_risk_score=score, risk_category=category,
        factor_scores=[RiskFactorScore(name="weather", raw_score=score, weight=1.0, weighted_contribution=score, reason="mock")],
        reasons=["mock"], assumptions=["mock"],
    )


# ---------------------------------------------------------------------------
# Pure calculation functions
# ---------------------------------------------------------------------------


class TestCalculations:
    def test_expected_waiting_cost(self) -> None:
        assert calculate_expected_waiting_cost(1000.0, 500.0, 4.0) == pytest.approx(6000.0)

    def test_adjusted_cost_with_zero_risk_weight(self) -> None:
        assert calculate_adjusted_cost(500_000.0, 90.0, 0.0) == pytest.approx(500_000.0)

    def test_adjusted_cost_with_risk_weight(self) -> None:
        assert calculate_adjusted_cost(500_000.0, 10.0, 100.0) == pytest.approx(501_000.0)

    def test_predicted_savings_per_mt(self) -> None:
        assert calculate_predicted_savings_per_mt(10.0, 7.0) == pytest.approx(3.0)

    def test_net_expected_benefit(self) -> None:
        assert calculate_net_expected_benefit(500_000.0, 480_000.0) == pytest.approx(20_000.0)


# ---------------------------------------------------------------------------
# BOOK_NOW default
# ---------------------------------------------------------------------------


class TestBookNowDefault:
    def test_single_vessel_no_forecast_books_now(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Alpha")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 20.0)],
            [_make_cost("V1", "MV Alpha", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Alpha", 20.0, RiskCategory.LOW)],
            cargo,
        )
        result = decision_engine.decide(ranked, cargo, current_route=route)
        assert result.recommended_action == DecisionAction.BOOK_NOW
        assert result.selected_vessel_id == "V1"
        assert result.expected_total_cost == pytest.approx(500_000.0)

    def test_raw_cost_preserved_not_replaced_by_adjusted(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        """RULE 8: expected_total_cost must remain the real dollar figure."""
        v = _make_vessel("V1", "MV Alpha")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 20.0)],
            [_make_cost("V1", "MV Alpha", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Alpha", 90.0, RiskCategory.SEVERE)],
            cargo,
        )
        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(risk_cost_per_point=1000.0, max_acceptable_risk_score=100.0),
        )
        # adjusted_cost includes the risk premium; expected_total_cost must not.
        assert result.expected_total_cost == pytest.approx(500_000.0)
        assert result.adjusted_cost == pytest.approx(500_000.0 + 90.0 * 1000.0)
        assert result.adjusted_cost != result.expected_total_cost


# ---------------------------------------------------------------------------
# SELECT_ALTERNATIVE_VESSEL (risk gate)
# ---------------------------------------------------------------------------


class TestAlternativeVessel:
    def test_switches_when_top_ranked_vessel_too_risky(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        risky = _make_vessel("V-RISKY", "MV Risky Best")
        safe = _make_vessel("V-SAFE", "MV Safe Second")
        ranked = ranking_engine.rank(
            [_make_voyage_result(risky, route, 20.0), _make_voyage_result(safe, route, 15.0)],
            [
                _make_cost("V-RISKY", "MV Risky Best", 400_000.0, 5.33),
                _make_cost("V-SAFE", "MV Safe Second", 420_000.0, 5.6),
            ],
            [
                _make_risk("V-RISKY", "MV Risky Best", 95.0, RiskCategory.SEVERE),
                _make_risk("V-SAFE", "MV Safe Second", 30.0, RiskCategory.MODERATE),
            ],
            cargo,
        )
        top_ranked_id = ranking_engine.feasible(ranked)[0].vessel_id
        assert top_ranked_id == "V-RISKY"  # cheaper -> ranks higher by Phase 5

        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(max_acceptable_risk_score=70.0),
        )
        assert result.recommended_action == DecisionAction.SELECT_ALTERNATIVE_VESSEL
        assert result.selected_vessel_id == "V-SAFE"

    def test_stays_with_top_vessel_when_risk_acceptable(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Fine")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 20.0)],
            [_make_cost("V1", "MV Fine", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Fine", 40.0, RiskCategory.MODERATE)],
            cargo,
        )
        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(max_acceptable_risk_score=70.0),
        )
        assert result.recommended_action == DecisionAction.BOOK_NOW
        assert result.selected_vessel_id == "V1"


# ---------------------------------------------------------------------------
# WAIT
# ---------------------------------------------------------------------------


class TestWaitDecision:
    def test_waits_when_forecast_is_favorable_and_deadline_safe(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Gamma")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 60.0)],  # huge buffer
            [_make_cost("V1", "MV Gamma", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Gamma", 15.0, RiskCategory.LOW)],
            cargo,
        )
        forecast = FreightForecastInput(
            current_freight_rate_per_mt=6.67, predicted_freight_rate_per_mt=3.0,
            forecast_horizon_days=5.0, confidence=0.9,
        )
        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(freight_forecast=forecast, waiting_cost_per_day=1_000.0),
        )
        assert result.recommended_action == DecisionAction.WAIT
        assert result.wait_vs_book_comparison is not None
        assert result.expected_savings is not None and result.expected_savings > 0

    def test_wait_result_has_populated_risk_category(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        """Regression test: risk_category was previously hardcoded to None
        for every action in _choose_best (found via the Phase 15 demo run,
        not by any prior test — this closes that gap)."""
        v = _make_vessel("V1", "MV Gamma")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 60.0)],
            [_make_cost("V1", "MV Gamma", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Gamma", 15.0, RiskCategory.LOW)],
            cargo,
        )
        forecast = FreightForecastInput(
            current_freight_rate_per_mt=6.67, predicted_freight_rate_per_mt=3.0,
            forecast_horizon_days=5.0, confidence=0.9,
        )
        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(freight_forecast=forecast, waiting_cost_per_day=1_000.0),
        )
        assert result.recommended_action == DecisionAction.WAIT
        assert result.risk_category is not None
        assert result.risk_category == RiskCategory.LOW

    def test_books_now_when_forecast_unfavorable(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Gamma")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 60.0)],
            [_make_cost("V1", "MV Gamma", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Gamma", 15.0, RiskCategory.LOW)],
            cargo,
        )
        forecast = FreightForecastInput(
            current_freight_rate_per_mt=6.67, predicted_freight_rate_per_mt=6.60,
            forecast_horizon_days=10.0, confidence=0.9,
        )
        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(freight_forecast=forecast, waiting_cost_per_day=5_000.0),
        )
        assert result.recommended_action == DecisionAction.BOOK_NOW

    def test_wait_excluded_when_it_breaks_the_deadline(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Tight")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 3.0)],  # tiny buffer
            [_make_cost("V1", "MV Tight", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Tight", 15.0, RiskCategory.LOW)],
            cargo,
        )
        forecast = FreightForecastInput(
            current_freight_rate_per_mt=6.67, predicted_freight_rate_per_mt=1.0,  # huge saving
            forecast_horizon_days=10.0, confidence=0.99,  # but 10-day wait blows the 3-day buffer
        )
        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(
                freight_forecast=forecast, waiting_cost_per_day=0.0,
                min_acceptable_deadline_buffer_days=0.0,
            ),
        )
        assert result.recommended_action == DecisionAction.BOOK_NOW
        wait_alt = next(a for a in result.alternatives if a.action == DecisionAction.WAIT)
        assert wait_alt.feasible_alternative is False

    def test_wait_excluded_when_confidence_too_low(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Gamma")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 60.0)],
            [_make_cost("V1", "MV Gamma", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Gamma", 15.0, RiskCategory.LOW)],
            cargo,
        )
        forecast = FreightForecastInput(
            current_freight_rate_per_mt=6.67, predicted_freight_rate_per_mt=3.0,
            forecast_horizon_days=5.0, confidence=0.2,
        )
        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(
                freight_forecast=forecast, waiting_cost_per_day=1_000.0,
                min_confidence_threshold=0.6,
            ),
        )
        assert result.recommended_action == DecisionAction.BOOK_NOW

    def test_no_forecast_means_no_wait_alternative_constructed(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Gamma")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 60.0)],
            [_make_cost("V1", "MV Gamma", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Gamma", 15.0, RiskCategory.LOW)],
            cargo,
        )
        result = decision_engine.decide(ranked, cargo, current_route=route)
        assert all(a.action != DecisionAction.WAIT for a in result.alternatives)


# ---------------------------------------------------------------------------
# NO_FEASIBLE_OPTION
# ---------------------------------------------------------------------------


class TestNoFeasibleOption:
    def test_no_feasible_vessels_returns_no_feasible_option(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Infeasible")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, -5.0, feasible=False)], [], [], cargo
        )
        result = decision_engine.decide(ranked, cargo, current_route=route)
        assert result.recommended_action == DecisionAction.NO_FEASIBLE_OPTION
        assert result.selected_vessel_id is None


# ---------------------------------------------------------------------------
# SELECT_ALTERNATIVE_ROUTE
# ---------------------------------------------------------------------------


class TestAlternativeRoute:
    def test_switches_route_when_meaningfully_better(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        route2 = Route(route_id="R2", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_600.0)

        v_r1 = _make_vessel("V-R1", "MV OnR1")
        ranked_r1 = ranking_engine.rank(
            [_make_voyage_result(v_r1, route, 10.0)],
            [_make_cost("V-R1", "MV OnR1", 900_000.0, 12.0, route_id="R1")],
            [_make_risk("V-R1", "MV OnR1", 20.0, RiskCategory.LOW, route_id="R1")],
            cargo,
        )

        v_r2 = _make_vessel("V-R2", "MV OnR2")
        ranked_r2 = ranking_engine.rank(
            [_make_voyage_result(v_r2, route2, 10.0)],
            [_make_cost("V-R2", "MV OnR2", 400_000.0, 5.33, route_id="R2")],
            [_make_risk("V-R2", "MV OnR2", 20.0, RiskCategory.LOW, route_id="R2")],
            cargo,
        )

        result = decision_engine.decide(
            ranked_r1, cargo, current_route=route,
            alternative_routes=[RouteCandidate(route=route2, ranked_vessels=ranked_r2)],
            decision_input=DecisionInput(min_switch_improvement_pct=5.0),
        )
        assert result.recommended_action == DecisionAction.SELECT_ALTERNATIVE_ROUTE
        assert result.selected_route is not None
        assert result.selected_route.route_id == "R2"

    def test_stays_on_current_route_when_alternative_not_better_enough(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        route2 = Route(route_id="R2", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_600.0)

        v_r1 = _make_vessel("V-R1", "MV OnR1")
        ranked_r1 = ranking_engine.rank(
            [_make_voyage_result(v_r1, route, 10.0)],
            [_make_cost("V-R1", "MV OnR1", 500_000.0, 6.67, route_id="R1")],
            [_make_risk("V-R1", "MV OnR1", 20.0, RiskCategory.LOW, route_id="R1")],
            cargo,
        )
        v_r2 = _make_vessel("V-R2", "MV OnR2")
        ranked_r2 = ranking_engine.rank(
            [_make_voyage_result(v_r2, route2, 10.0)],
            [_make_cost("V-R2", "MV OnR2", 499_000.0, 6.65, route_id="R2")],  # negligibly cheaper
            [_make_risk("V-R2", "MV OnR2", 20.0, RiskCategory.LOW, route_id="R2")],
            cargo,
        )
        result = decision_engine.decide(
            ranked_r1, cargo, current_route=route,
            alternative_routes=[RouteCandidate(route=route2, ranked_vessels=ranked_r2)],
            decision_input=DecisionInput(min_switch_improvement_pct=5.0),
        )
        assert result.recommended_action == DecisionAction.BOOK_NOW
        assert result.selected_vessel_id == "V-R1"

    def test_no_alternative_routes_never_triggers_route_switch(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Solo")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 10.0)],
            [_make_cost("V1", "MV Solo", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Solo", 20.0, RiskCategory.LOW)],
            cargo,
        )
        result = decision_engine.decide(ranked, cargo, current_route=route)
        assert result.recommended_action != DecisionAction.SELECT_ALTERNATIVE_ROUTE
        assert all(a.action != DecisionAction.SELECT_ALTERNATIVE_ROUTE for a in result.alternatives)


# ---------------------------------------------------------------------------
# "Compare, don't cascade"
# ---------------------------------------------------------------------------


class TestCompareAllAlternatives:
    def test_all_alternatives_are_reported_not_just_the_winner(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v1 = _make_vessel("V1", "MV One")
        v2 = _make_vessel("V2", "MV Two")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v1, route, 30.0), _make_voyage_result(v2, route, 20.0)],
            [
                _make_cost("V1", "MV One", 500_000.0, 6.67),
                _make_cost("V2", "MV Two", 550_000.0, 7.33),
            ],
            [
                _make_risk("V1", "MV One", 20.0, RiskCategory.LOW),
                _make_risk("V2", "MV Two", 25.0, RiskCategory.LOW),
            ],
            cargo,
        )
        forecast = FreightForecastInput(
            current_freight_rate_per_mt=6.67, predicted_freight_rate_per_mt=6.5,
            forecast_horizon_days=3.0, confidence=0.8,
        )
        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(freight_forecast=forecast),
        )
        # Both BOOK_NOW alternatives (one per vessel) AND the WAIT alternative
        # must all appear, regardless of which one wins.
        actions_seen = {a.action for a in result.alternatives}
        assert DecisionAction.BOOK_NOW in actions_seen
        assert DecisionAction.WAIT in actions_seen
        assert len(result.alternatives) >= 3  # 2 vessels booked now + 1 wait

    def test_excluded_alternatives_are_still_visible_with_reason(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Tight")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 2.0)],
            [_make_cost("V1", "MV Tight", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Tight", 15.0, RiskCategory.LOW)],
            cargo,
        )
        forecast = FreightForecastInput(
            current_freight_rate_per_mt=6.67, predicted_freight_rate_per_mt=1.0,
            forecast_horizon_days=10.0, confidence=0.99,
        )
        result = decision_engine.decide(
            ranked, cargo, current_route=route,
            decision_input=DecisionInput(freight_forecast=forecast, waiting_cost_per_day=0.0),
        )
        wait_alt = next(a for a in result.alternatives if a.action == DecisionAction.WAIT)
        assert wait_alt.feasible_alternative is False
        assert wait_alt.notes  # reason is visible, not silently dropped
        assert any("Excluded" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_identical_inputs_produce_identical_decision(
        self, decision_engine, ranking_engine, cargo, route
    ) -> None:
        v = _make_vessel("V1", "MV Alpha")
        ranked = ranking_engine.rank(
            [_make_voyage_result(v, route, 20.0)],
            [_make_cost("V1", "MV Alpha", 500_000.0, 6.67)],
            [_make_risk("V1", "MV Alpha", 20.0, RiskCategory.LOW)],
            cargo,
        )
        r1 = decision_engine.decide(ranked, cargo, current_route=route)
        r2 = decision_engine.decide(ranked, cargo, current_route=route)
        assert r1.recommended_action == r2.recommended_action
        assert r1.expected_total_cost == r2.expected_total_cost
        assert r1.adjusted_cost == r2.adjusted_cost
