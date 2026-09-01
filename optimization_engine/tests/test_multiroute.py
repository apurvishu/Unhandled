"""
Tests for the multi-route comparison engine (Phase 8).

Tests cover:
    - Routes with no feasible vessel are excluded (never scored/ranked)
    - Cheapest route does not automatically win
    - Congestion is compared only when every feasible route supplies it
    - Emissions is compared only when every feasible route supplies it
    - Configurable weights
    - Deterministic tie-breaking
    - Raw metrics preserved alongside normalized scores
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from optimization_engine.domain.models import Cargo, Route, Vessel, VesselStatus, VoyageFeasibilityResult
from optimization_engine.economics.models import VoyageCostBreakdown
from optimization_engine.multiroute.engine import MultiRouteEngine
from optimization_engine.multiroute.models import RouteCandidate, RouteWeights
from optimization_engine.ranking.engine import RankingEngine
from optimization_engine.risk.models import RiskAssessmentResult, RiskCategory, RiskFactorScore


@pytest.fixture
def engine() -> MultiRouteEngine:
    return MultiRouteEngine()


@pytest.fixture
def ranking_engine() -> RankingEngine:
    return RankingEngine()


@pytest.fixture
def cargo() -> Cargo:
    return Cargo(
        cargo_id="TEST-MR-001", cargo_type="iron_ore", quantity_mt=75_000.0,
        origin_port="CNSHA", destination_port="INPRT",
        required_arrival_date=date(2026, 10, 15), hazardous=False,
    )


def _make_vessel(vessel_id: str, name: str) -> Vessel:
    return Vessel(
        vessel_id=vessel_id, vessel_name=name, imo=f"IMO{vessel_id}", mmsi=f"MMSI{vessel_id}",
        vessel_type="bulk_carrier", dwt_mt=95_000.0, cargo_capacity_mt=85_000.0,
        loa_m=250.0, beam_m=43.0, draft_m=14.0, speed_knots=14.5, current_location="Singapore",
        status=VesselStatus.AVAILABLE, available_from=date(2026, 8, 1), cargo_types_supported=["iron_ore"],
    )


def _make_voyage(vessel: Vessel, route: Route, buffer_days: float, feasible: bool = True) -> VoyageFeasibilityResult:
    return VoyageFeasibilityResult(
        vessel=vessel, route=route, estimated_departure=datetime(2026, 8, 1, 0, 0),
        sailing_hours=237.93, sailing_days=9.91, estimated_arrival=datetime(2026, 8, 10, 21, 56),
        required_arrival=date(2026, 10, 15), deadline_buffer_days=buffer_days,
        deadline_feasible=feasible, phase1_feasible=feasible, feasible=feasible,
        reasons=[] if feasible else ["mock rejection"], assumptions=["mock"],
    )


def _make_cost(vessel_id: str, name: str, total_cost: float, route_id: str) -> VoyageCostBreakdown:
    return VoyageCostBreakdown(
        vessel_name=name, vessel_id=vessel_id, route_id=route_id,
        charter_cost=total_cost * 0.5, fuel_consumed_mt=500.0, fuel_cost=total_cost * 0.3,
        port_cost=1_000.0, berth_cost=1_000.0, pilotage_cost=500.0, tug_cost=500.0,
        cargo_handling_cost=2_000.0, waiting_cost=0.0, demurrage_cost=0.0, storage_cost=0.0,
        insurance_cost=1_000.0, maintenance_cost=1_000.0, tax_cost=0.0, duty_cost=0.0, other_cost=0.0,
        total_cost=total_cost, cost_per_mt=total_cost / 75_000.0, currency="USD", assumptions=["mock"],
    )


def _make_risk(
    vessel_id: str, name: str, score: float, category: RiskCategory, route_id: str, congestion: float = 20.0
) -> RiskAssessmentResult:
    return RiskAssessmentResult(
        vessel_id=vessel_id, vessel_name=name, cargo_id="TEST-MR-001", route_id=route_id,
        overall_risk_score=score, risk_category=category,
        factor_scores=[
            RiskFactorScore(name="weather", raw_score=score, weight=0.5, weighted_contribution=score * 0.5, reason="mock"),
            RiskFactorScore(name="congestion", raw_score=congestion, weight=0.5, weighted_contribution=congestion * 0.5, reason="mock"),
        ],
        reasons=["mock"], assumptions=["mock"],
    )


def _build_candidate(ranking_engine, route, vessel_id, vessel_name, total_cost, risk_score, buffer_days, congestion=20.0, feasible=True):
    vessel = _make_vessel(vessel_id, vessel_name)
    voyage = _make_voyage(vessel, route, buffer_days, feasible=feasible)
    if not feasible:
        ranked = ranking_engine.rank([voyage], [], [], Cargo(
            cargo_id="TEST-MR-001", cargo_type="iron_ore", quantity_mt=75_000.0,
            origin_port="CNSHA", destination_port="INPRT",
            required_arrival_date=date(2026, 10, 15), hazardous=False,
        ))
        return RouteCandidate(route=route, ranked_vessels=ranked, risk_results=[])
    cost = _make_cost(vessel_id, vessel_name, total_cost, route.route_id)
    risk = _make_risk(vessel_id, vessel_name, risk_score, RiskCategory.LOW, route.route_id, congestion=congestion)
    ranked = ranking_engine.rank(
        [voyage], [cost], [risk],
        Cargo(cargo_id="TEST-MR-001", cargo_type="iron_ore", quantity_mt=75_000.0,
              origin_port="CNSHA", destination_port="INPRT",
              required_arrival_date=date(2026, 10, 15), hazardous=False),
    )
    return RouteCandidate(route=route, ranked_vessels=ranked, risk_results=[risk])


# ---------------------------------------------------------------------------
# Infeasible routes excluded
# ---------------------------------------------------------------------------


class TestInfeasibleRouteExclusion:
    def test_route_with_no_feasible_vessel_excluded(self, engine, ranking_engine, cargo):
        route_ok = Route(route_id="R-OK", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        route_bad = Route(route_id="R-BAD", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=10_000.0)

        cand_ok = _build_candidate(ranking_engine, route_ok, "V1", "MV OK", 500_000.0, 20.0, 10.0)
        cand_bad = _build_candidate(ranking_engine, route_bad, "V2", "MV Bad", 0, 0, -50.0, feasible=False)

        ranked = engine.compare([cand_ok, cand_bad], cargo)
        assert len(engine.feasible(ranked)) == 1
        assert engine.feasible(ranked)[0].route.route_id == "R-OK"
        excluded = engine.excluded(ranked)
        assert len(excluded) == 1
        assert excluded[0].route.route_id == "R-BAD"
        assert excluded[0].rank is None
        assert excluded[0].overall_score is None

    def test_all_infeasible_returns_empty_feasible_list(self, engine, ranking_engine, cargo):
        route_bad = Route(route_id="R-BAD", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=10_000.0)
        cand_bad = _build_candidate(ranking_engine, route_bad, "V1", "MV Bad", 0, 0, -50.0, feasible=False)
        ranked = engine.compare([cand_bad], cargo)
        assert engine.feasible(ranked) == []
        assert len(engine.excluded(ranked)) == 1


# ---------------------------------------------------------------------------
# Cheapest doesn't automatically win
# ---------------------------------------------------------------------------


class TestCheapestDoesNotAutoWin:
    def test_cheaper_route_can_lose_on_risk_and_buffer(self, engine, ranking_engine, cargo):
        cheap_route = Route(route_id="R-CHEAP", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=2_000.0)
        safe_route = Route(route_id="R-SAFE", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)

        cand_cheap = _build_candidate(ranking_engine, cheap_route, "V1", "MV Cheap", 400_000.0, 95.0, 5.0)
        cand_safe = _build_candidate(ranking_engine, safe_route, "V2", "MV Safe", 500_000.0, 5.0, 40.0)

        risk_and_buffer_only = RouteWeights(cost=0, risk=0.5, deadline_buffer=0.5, congestion=0, emissions=0)
        ranked = engine.compare([cand_cheap, cand_safe], cargo, weights=risk_and_buffer_only)
        winner = engine.feasible(ranked)[0]
        assert winner.route.route_id == "R-SAFE"

    def test_default_weights_do_not_let_cost_fully_dominate(self, engine, ranking_engine, cargo):
        cheap_risky = Route(route_id="R-CHEAP", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=2_000.0)
        pricier_safe = Route(route_id="R-SAFE", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        cand_cheap = _build_candidate(ranking_engine, cheap_risky, "V1", "MV CheapRisky", 300_000.0, 100.0, 5.0)
        cand_safe = _build_candidate(ranking_engine, pricier_safe, "V2", "MV PricierSafe", 310_000.0, 0.0, 40.0)
        # Cost weight (0.35 default) alone cannot overcome risk(0.25)+buffer(0.25) both favoring the safe route.
        ranked = engine.compare([cand_cheap, cand_safe], cargo)
        winner = engine.feasible(ranked)[0]
        assert winner.route.route_id == "R-SAFE"


# ---------------------------------------------------------------------------
# Optional data (congestion, emissions) dropped when unavailable
# ---------------------------------------------------------------------------


class TestOptionalDataHandling:
    def test_congestion_compared_when_all_routes_supply_it(self, engine, ranking_engine, cargo):
        r1 = Route(route_id="R1", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        r2 = Route(route_id="R2", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        cand1 = _build_candidate(ranking_engine, r1, "V1", "MV One", 500_000.0, 20.0, 10.0, congestion=10.0)
        cand2 = _build_candidate(ranking_engine, r2, "V2", "MV Two", 500_000.0, 20.0, 10.0, congestion=90.0)
        ranked = engine.compare([cand1, cand2], cargo)
        for r in engine.feasible(ranked):
            names = {c.name for c in r.component_scores}
            assert "congestion" in names

    def test_congestion_excluded_when_risk_results_missing(self, engine, ranking_engine, cargo):
        r1 = Route(route_id="R1", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        vessel = _make_vessel("V1", "MV One")
        voyage = _make_voyage(vessel, r1, 10.0)
        cost = _make_cost("V1", "MV One", 500_000.0, "R1")
        risk = _make_risk("V1", "MV One", 20.0, RiskCategory.LOW, "R1")
        ranked_vessels = ranking_engine.rank([voyage], [cost], [risk], cargo)
        # No risk_results supplied on the candidate -> congestion cannot be extracted.
        candidate = RouteCandidate(route=r1, ranked_vessels=ranked_vessels, risk_results=[])
        ranked = engine.compare([candidate], cargo)
        names = {c.name for c in engine.feasible(ranked)[0].component_scores}
        assert "congestion" not in names

    def test_emissions_excluded_when_not_all_routes_supply_it(self, engine, ranking_engine, cargo):
        r1 = Route(route_id="R1", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        r2 = Route(route_id="R2", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        cand1 = _build_candidate(ranking_engine, r1, "V1", "MV One", 500_000.0, 20.0, 10.0)
        cand2 = _build_candidate(ranking_engine, r2, "V2", "MV Two", 500_000.0, 20.0, 10.0)
        cand1 = cand1.model_copy(update={"emissions_co2_kg": 1000.0})
        # cand2 has no emissions figure -> must be excluded from comparison for BOTH
        ranked = engine.compare([cand1, cand2], cargo)
        for r in engine.feasible(ranked):
            names = {c.name for c in r.component_scores}
            assert "emissions" not in names

    def test_emissions_compared_when_all_routes_supply_it(self, engine, ranking_engine, cargo):
        r1 = Route(route_id="R1", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        r2 = Route(route_id="R2", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        cand1 = _build_candidate(ranking_engine, r1, "V1", "MV One", 500_000.0, 20.0, 10.0)
        cand2 = _build_candidate(ranking_engine, r2, "V2", "MV Two", 500_000.0, 20.0, 10.0)
        cand1 = cand1.model_copy(update={"emissions_co2_kg": 1000.0})
        cand2 = cand2.model_copy(update={"emissions_co2_kg": 2000.0})
        ranked = engine.compare([cand1, cand2], cargo)
        for r in engine.feasible(ranked):
            names = {c.name for c in r.component_scores}
            assert "emissions" in names


# ---------------------------------------------------------------------------
# Determinism and raw metrics preserved
# ---------------------------------------------------------------------------


class TestDeterminismAndRawMetrics:
    def test_repeated_runs_produce_identical_order(self, engine, ranking_engine, cargo):
        r1 = Route(route_id="R1", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        r2 = Route(route_id="R2", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_500.0)
        cand1 = _build_candidate(ranking_engine, r1, "V1", "MV One", 500_000.0, 20.0, 10.0)
        cand2 = _build_candidate(ranking_engine, r2, "V2", "MV Two", 600_000.0, 30.0, 15.0)
        run1 = [r.route.route_id for r in engine.feasible(engine.compare([cand1, cand2], cargo))]
        run2 = [r.route.route_id for r in engine.feasible(engine.compare([cand1, cand2], cargo))]
        assert run1 == run2

    def test_raw_metrics_preserved_alongside_scores(self, engine, ranking_engine, cargo):
        r1 = Route(route_id="R1", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_000.0)
        cand1 = _build_candidate(ranking_engine, r1, "V1", "MV One", 500_000.0, 20.0, 10.0)
        ranked = engine.feasible(engine.compare([cand1], cargo))
        assert ranked[0].raw_metrics.total_cost == pytest.approx(500_000.0)
        assert ranked[0].raw_metrics.overall_risk_score == pytest.approx(20.0)
        assert ranked[0].raw_metrics.best_vessel_id == "V1"
