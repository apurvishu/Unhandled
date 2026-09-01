"""
Tests for the vessel ranking engine (Phase 5).

Tests cover:
    - Infeasible vessels are excluded from ranking (never scored/ranked)
    - Cost direction (cheaper scores higher)
    - Risk direction (lower risk scores higher)
    - Deadline-buffer effect (more buffer scores higher)
    - Configurable weights change the outcome
    - Deterministic tie-breaking
    - Explanations (reasons are present and calculation-grounded)
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from optimization_engine.domain.models import Cargo, Route, Vessel, VesselStatus, VoyageFeasibilityResult
from optimization_engine.economics.models import VoyageCostBreakdown
from optimization_engine.ranking.calculations import (
    calculate_availability_score,
    calculate_batch_relative_score,
    calculate_cargo_suitability_score,
    calculate_operational_suitability_score,
    normalize_weights,
)
from optimization_engine.ranking.engine import RankingEngine
from optimization_engine.ranking.models import RankedVessel, RankingWeights
from optimization_engine.risk.models import RiskAssessmentResult, RiskCategory, RiskFactorScore


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> RankingEngine:
    return RankingEngine()


@pytest.fixture
def cargo() -> Cargo:
    return Cargo(
        cargo_id="TEST-RANK-001",
        cargo_type="iron_ore",
        quantity_mt=75_000.0,
        origin_port="CNSHA",
        destination_port="INPRT",
        required_arrival_date=date(2026, 10, 15),
        hazardous=False,
    )


@pytest.fixture
def route() -> Route:
    return Route(
        route_id="CNSHA-INPRT",
        origin_port_id="CNSHA",
        destination_port_id="INPRT",
        distance_nm=3_450.0,
    )


def _make_vessel(
    vessel_id: str,
    name: str,
    capacity_mt: float = 85_000.0,
    status: VesselStatus = VesselStatus.AVAILABLE,
    available_from: date = date(2026, 8, 1),
) -> Vessel:
    return Vessel(
        vessel_id=vessel_id,
        vessel_name=name,
        imo=f"IMO{vessel_id}",
        mmsi=f"MMSI{vessel_id}",
        vessel_type="bulk_carrier",
        dwt_mt=capacity_mt + 10_000,
        cargo_capacity_mt=capacity_mt,
        loa_m=250.0,
        beam_m=43.0,
        draft_m=14.0,
        speed_knots=14.5,
        current_location="Singapore Anchorage",
        status=status,
        available_from=available_from,
        cargo_types_supported=["iron_ore", "coal"],
    )


def _make_voyage_result(
    vessel: Vessel, route: Route, deadline_buffer_days: float = 10.0, feasible: bool = True,
    reasons: list[str] | None = None,
) -> VoyageFeasibilityResult:
    return VoyageFeasibilityResult(
        vessel=vessel,
        route=route,
        estimated_departure=datetime(2026, 8, 1, 0, 0),
        sailing_hours=237.93,
        sailing_days=9.91,
        estimated_arrival=datetime(2026, 8, 10, 21, 56),
        required_arrival=date(2026, 10, 15),
        deadline_buffer_days=deadline_buffer_days,
        deadline_feasible=feasible,
        phase1_feasible=feasible,
        feasible=feasible,
        reasons=reasons or [],
        assumptions=["mock"],
    )


def _make_cost(vessel_id: str, name: str, total_cost: float, cost_per_mt: float) -> VoyageCostBreakdown:
    return VoyageCostBreakdown(
        vessel_name=name,
        vessel_id=vessel_id,
        route_id="CNSHA-INPRT",
        charter_cost=total_cost * 0.5,
        fuel_consumed_mt=500.0,
        fuel_cost=total_cost * 0.3,
        port_cost=1_000.0,
        berth_cost=1_000.0,
        pilotage_cost=500.0,
        tug_cost=500.0,
        cargo_handling_cost=2_000.0,
        waiting_cost=0.0,
        demurrage_cost=0.0,
        storage_cost=0.0,
        insurance_cost=1_000.0,
        maintenance_cost=1_000.0,
        tax_cost=0.0,
        duty_cost=0.0,
        other_cost=0.0,
        total_cost=total_cost,
        cost_per_mt=cost_per_mt,
        currency="USD",
        assumptions=["mock"],
    )


def _make_risk(vessel_id: str, name: str, score: float, category: RiskCategory) -> RiskAssessmentResult:
    return RiskAssessmentResult(
        vessel_id=vessel_id,
        vessel_name=name,
        cargo_id="TEST-RANK-001",
        route_id="CNSHA-INPRT",
        overall_risk_score=score,
        risk_category=category,
        factor_scores=[
            RiskFactorScore(
                name="weather", raw_score=score, weight=1.0,
                weighted_contribution=score, reason="mock",
            )
        ],
        reasons=["mock reason"],
        assumptions=["mock"],
    )


# ---------------------------------------------------------------------------
# Pure calculation functions
# ---------------------------------------------------------------------------


class TestBatchRelativeScore:
    def test_all_equal_scores_hundred(self) -> None:
        assert calculate_batch_relative_score(50.0, 50.0, 50.0, higher_is_better=True) == 100.0

    def test_lower_is_better_best_scores_hundred(self) -> None:
        assert calculate_batch_relative_score(0.0, 0.0, 100.0, higher_is_better=False) == 100.0

    def test_lower_is_better_worst_scores_zero(self) -> None:
        assert calculate_batch_relative_score(100.0, 0.0, 100.0, higher_is_better=False) == 0.0

    def test_higher_is_better_best_scores_hundred(self) -> None:
        assert calculate_batch_relative_score(100.0, 0.0, 100.0, higher_is_better=True) == 100.0

    def test_higher_is_better_worst_scores_zero(self) -> None:
        assert calculate_batch_relative_score(0.0, 0.0, 100.0, higher_is_better=True) == 0.0

    def test_midpoint_scores_fifty(self) -> None:
        assert calculate_batch_relative_score(50.0, 0.0, 100.0, higher_is_better=True) == pytest.approx(50.0)


class TestCargoSuitability:
    def test_full_utilization_scores_hundred(self) -> None:
        assert calculate_cargo_suitability_score(1.0) == 100.0

    def test_half_utilization_scores_fifty(self) -> None:
        assert calculate_cargo_suitability_score(0.5) == 50.0


class TestAvailabilityScore:
    def test_full_lead_time_scores_hundred(self) -> None:
        assert calculate_availability_score(30.0) == 100.0

    def test_zero_lead_time_scores_zero(self) -> None:
        assert calculate_availability_score(0.0) == 0.0

    def test_negative_lead_time_clamps_to_zero(self) -> None:
        assert calculate_availability_score(-10.0) == 0.0

    def test_partial_lead_time(self) -> None:
        assert calculate_availability_score(15.0) == pytest.approx(50.0)


class TestOperationalSuitability:
    def test_available_scores_highest(self) -> None:
        assert calculate_operational_suitability_score(VesselStatus.AVAILABLE) == 100.0

    def test_en_route_scores_lower_than_available(self) -> None:
        assert calculate_operational_suitability_score(
            VesselStatus.EN_ROUTE
        ) < calculate_operational_suitability_score(VesselStatus.AVAILABLE)


class TestWeightNormalization:
    def test_normalizes_to_one(self) -> None:
        result = normalize_weights({"a": 3.0, "b": 1.0})
        assert sum(result.values()) == pytest.approx(1.0)

    def test_zero_total_rejected(self) -> None:
        with pytest.raises(ValueError, match="Total weight must be > 0"):
            normalize_weights({"a": 0.0})


# ---------------------------------------------------------------------------
# Infeasible vessels excluded
# ---------------------------------------------------------------------------


class TestInfeasibleExclusion:
    def test_infeasible_vessel_not_ranked(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        feasible_vessel = _make_vessel("V1", "MV Feasible")
        infeasible_vessel = _make_vessel("V2", "MV Infeasible")

        voyage_results = [
            _make_voyage_result(feasible_vessel, route, deadline_buffer_days=10.0),
            _make_voyage_result(
                infeasible_vessel, route, deadline_buffer_days=-5.0, feasible=False,
                reasons=["Arrives after deadline"],
            ),
        ]
        cost_results = [_make_cost("V1", "MV Feasible", 500_000.0, 6.67)]
        risk_results = [_make_risk("V1", "MV Feasible", 20.0, RiskCategory.LOW)]

        ranked = engine.rank(voyage_results, cost_results, risk_results, cargo)
        excluded = engine.excluded(ranked)
        feasible = engine.feasible(ranked)

        assert len(excluded) == 1
        assert excluded[0].vessel_id == "V2"
        assert excluded[0].rank is None
        assert excluded[0].overall_score is None
        assert excluded[0].component_scores == []
        assert excluded[0].raw_metrics is None

        assert len(feasible) == 1
        assert feasible[0].vessel_id == "V1"
        assert feasible[0].rank == 1

    def test_infeasible_vessel_never_outranks_feasible_regardless_of_raw_numbers(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        """A structural guarantee: infeasible vessels can never appear in
        feasible()'s output, no matter how favorable their hypothetical
        metrics would have been."""
        ok_vessel = _make_vessel("V1", "MV OK", capacity_mt=76_000.0)
        infeasible_vessel = _make_vessel("V2", "MV Would Be Great", capacity_mt=75_001.0)

        voyage_results = [
            _make_voyage_result(ok_vessel, route, deadline_buffer_days=1.0),
            _make_voyage_result(
                infeasible_vessel, route, deadline_buffer_days=100.0, feasible=False,
                reasons=["Rejected at Phase 1"],
            ),
        ]
        cost_results = [_make_cost("V1", "MV OK", 900_000.0, 11.84)]
        risk_results = [_make_risk("V1", "MV OK", 80.0, RiskCategory.HIGH)]

        ranked = engine.rank(voyage_results, cost_results, risk_results, cargo)
        feasible = engine.feasible(ranked)

        assert len(feasible) == 1
        assert feasible[0].vessel_id == "V1"

    def test_all_infeasible_returns_empty_feasible_list(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v = _make_vessel("V1", "MV None Feasible")
        voyage_results = [_make_voyage_result(v, route, feasible=False, reasons=["rejected"])]
        ranked = engine.rank(voyage_results, [], [], cargo)
        assert engine.feasible(ranked) == []
        assert len(engine.excluded(ranked)) == 1


# ---------------------------------------------------------------------------
# Cost direction
# ---------------------------------------------------------------------------


class TestCostDirection:
    def test_cheaper_vessel_scores_higher_when_all_else_equal(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        cheap = _make_vessel("V1", "MV Cheap")
        expensive = _make_vessel("V2", "MV Expensive")

        voyage_results = [
            _make_voyage_result(cheap, route, deadline_buffer_days=10.0),
            _make_voyage_result(expensive, route, deadline_buffer_days=10.0),
        ]
        cost_results = [
            _make_cost("V1", "MV Cheap", 400_000.0, 5.33),
            _make_cost("V2", "MV Expensive", 800_000.0, 10.67),
        ]
        risk_results = [
            _make_risk("V1", "MV Cheap", 20.0, RiskCategory.LOW),
            _make_risk("V2", "MV Expensive", 20.0, RiskCategory.LOW),
        ]

        ranked = engine.feasible(engine.rank(voyage_results, cost_results, risk_results, cargo))
        cost_only = RankingWeights(
            cost=1.0, risk=0, deadline_buffer=0, cargo_suitability=0,
            availability=0, operational_suitability=0,
        )
        ranked_cost_only = engine.feasible(
            engine.rank(voyage_results, cost_results, risk_results, cargo, weights=cost_only)
        )

        assert ranked_cost_only[0].vessel_id == "V1"
        assert ranked_cost_only[0].overall_score == pytest.approx(100.0)
        assert ranked_cost_only[1].overall_score == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Risk direction
# ---------------------------------------------------------------------------


class TestRiskDirection:
    def test_lower_risk_vessel_scores_higher(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        safe = _make_vessel("V1", "MV Safe")
        risky = _make_vessel("V2", "MV Risky")

        voyage_results = [
            _make_voyage_result(safe, route, deadline_buffer_days=10.0),
            _make_voyage_result(risky, route, deadline_buffer_days=10.0),
        ]
        cost_results = [
            _make_cost("V1", "MV Safe", 500_000.0, 6.67),
            _make_cost("V2", "MV Risky", 500_000.0, 6.67),
        ]
        risk_results = [
            _make_risk("V1", "MV Safe", 10.0, RiskCategory.LOW),
            _make_risk("V2", "MV Risky", 90.0, RiskCategory.SEVERE),
        ]

        risk_only = RankingWeights(
            cost=0, risk=1.0, deadline_buffer=0, cargo_suitability=0,
            availability=0, operational_suitability=0,
        )
        ranked = engine.feasible(
            engine.rank(voyage_results, cost_results, risk_results, cargo, weights=risk_only)
        )

        assert ranked[0].vessel_id == "V1"
        assert ranked[0].overall_score == pytest.approx(100.0)
        assert ranked[1].overall_score == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Deadline-buffer effect
# ---------------------------------------------------------------------------


class TestDeadlineBufferEffect:
    def test_larger_buffer_scores_higher(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        early = _make_vessel("V1", "MV Early")
        late = _make_vessel("V2", "MV Barely On Time")

        voyage_results = [
            _make_voyage_result(early, route, deadline_buffer_days=25.0),
            _make_voyage_result(late, route, deadline_buffer_days=1.0),
        ]
        cost_results = [
            _make_cost("V1", "MV Early", 500_000.0, 6.67),
            _make_cost("V2", "MV Barely On Time", 500_000.0, 6.67),
        ]
        risk_results = [
            _make_risk("V1", "MV Early", 20.0, RiskCategory.LOW),
            _make_risk("V2", "MV Barely On Time", 20.0, RiskCategory.LOW),
        ]

        buffer_only = RankingWeights(
            cost=0, risk=0, deadline_buffer=1.0, cargo_suitability=0,
            availability=0, operational_suitability=0,
        )
        ranked = engine.feasible(
            engine.rank(voyage_results, cost_results, risk_results, cargo, weights=buffer_only)
        )

        assert ranked[0].vessel_id == "V1"
        assert ranked[0].overall_score == pytest.approx(100.0)
        assert ranked[1].overall_score == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Configurable weights
# ---------------------------------------------------------------------------


class TestConfigurableWeights:
    def test_changing_weights_changes_winner(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        """A vessel that's cheap-but-risky can win under cost-only weights
        and lose under risk-only weights."""
        cheap_risky = _make_vessel("V1", "MV Cheap Risky")
        pricey_safe = _make_vessel("V2", "MV Pricey Safe")

        voyage_results = [
            _make_voyage_result(cheap_risky, route, deadline_buffer_days=10.0),
            _make_voyage_result(pricey_safe, route, deadline_buffer_days=10.0),
        ]
        cost_results = [
            _make_cost("V1", "MV Cheap Risky", 300_000.0, 4.0),
            _make_cost("V2", "MV Pricey Safe", 900_000.0, 12.0),
        ]
        risk_results = [
            _make_risk("V1", "MV Cheap Risky", 90.0, RiskCategory.SEVERE),
            _make_risk("V2", "MV Pricey Safe", 5.0, RiskCategory.LOW),
        ]

        cost_only = RankingWeights(
            cost=1.0, risk=0, deadline_buffer=0, cargo_suitability=0,
            availability=0, operational_suitability=0,
        )
        risk_only = RankingWeights(
            cost=0, risk=1.0, deadline_buffer=0, cargo_suitability=0,
            availability=0, operational_suitability=0,
        )

        winner_by_cost = engine.feasible(
            engine.rank(voyage_results, cost_results, risk_results, cargo, weights=cost_only)
        )[0]
        winner_by_risk = engine.feasible(
            engine.rank(voyage_results, cost_results, risk_results, cargo, weights=risk_only)
        )[0]

        assert winner_by_cost.vessel_id == "V1"
        assert winner_by_risk.vessel_id == "V2"

    def test_default_weights_used_when_none_supplied(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v1 = _make_vessel("V1", "MV One")
        voyage_results = [_make_voyage_result(v1, route)]
        cost_results = [_make_cost("V1", "MV One", 500_000.0, 6.67)]
        risk_results = [_make_risk("V1", "MV One", 20.0, RiskCategory.LOW)]
        ranked = engine.feasible(engine.rank(voyage_results, cost_results, risk_results, cargo))
        assert len(ranked[0].component_scores) == 6

    def test_weights_not_summing_to_one_are_normalized(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v1 = _make_vessel("V1", "MV One")
        voyage_results = [_make_voyage_result(v1, route)]
        cost_results = [_make_cost("V1", "MV One", 500_000.0, 6.67)]
        risk_results = [_make_risk("V1", "MV One", 20.0, RiskCategory.LOW)]
        heavy = RankingWeights(
            cost=5.0, risk=5.0, deadline_buffer=5.0, cargo_suitability=5.0,
            availability=5.0, operational_suitability=5.0,
        )
        ranked = engine.feasible(
            engine.rank(voyage_results, cost_results, risk_results, cargo, weights=heavy)
        )
        assert 0.0 <= ranked[0].overall_score <= 100.0
        assert sum(c.weight for c in ranked[0].component_scores) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Deterministic ties
# ---------------------------------------------------------------------------


class TestDeterministicTies:
    def test_identical_vessels_break_tie_by_vessel_id(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        twin_b = _make_vessel("V-B", "MV Twin B")
        twin_a = _make_vessel("V-A", "MV Twin A")

        voyage_results = [
            _make_voyage_result(twin_b, route, deadline_buffer_days=10.0),
            _make_voyage_result(twin_a, route, deadline_buffer_days=10.0),
        ]
        cost_results = [
            _make_cost("V-B", "MV Twin B", 500_000.0, 6.67),
            _make_cost("V-A", "MV Twin A", 500_000.0, 6.67),
        ]
        risk_results = [
            _make_risk("V-B", "MV Twin B", 20.0, RiskCategory.LOW),
            _make_risk("V-A", "MV Twin A", 20.0, RiskCategory.LOW),
        ]

        ranked = engine.feasible(engine.rank(voyage_results, cost_results, risk_results, cargo))
        assert ranked[0].overall_score == pytest.approx(ranked[1].overall_score)
        assert ranked[0].vessel_id == "V-A"  # lexicographically first wins the tie
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2

    def test_repeated_runs_produce_identical_order(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v1 = _make_vessel("V1", "MV A")
        v2 = _make_vessel("V2", "MV B")
        voyage_results = [
            _make_voyage_result(v1, route, deadline_buffer_days=10.0),
            _make_voyage_result(v2, route, deadline_buffer_days=20.0),
        ]
        cost_results = [
            _make_cost("V1", "MV A", 500_000.0, 6.67),
            _make_cost("V2", "MV B", 600_000.0, 8.0),
        ]
        risk_results = [
            _make_risk("V1", "MV A", 20.0, RiskCategory.LOW),
            _make_risk("V2", "MV B", 30.0, RiskCategory.MODERATE),
        ]

        run1 = [rv.vessel_id for rv in engine.feasible(engine.rank(voyage_results, cost_results, risk_results, cargo))]
        run2 = [rv.vessel_id for rv in engine.feasible(engine.rank(voyage_results, cost_results, risk_results, cargo))]
        assert run1 == run2


# ---------------------------------------------------------------------------
# Explanations
# ---------------------------------------------------------------------------


class TestExplanations:
    def test_reasons_mention_rank_position(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v1 = _make_vessel("V1", "MV One")
        voyage_results = [_make_voyage_result(v1, route)]
        cost_results = [_make_cost("V1", "MV One", 500_000.0, 6.67)]
        risk_results = [_make_risk("V1", "MV One", 20.0, RiskCategory.LOW)]
        ranked = engine.feasible(engine.rank(voyage_results, cost_results, risk_results, cargo))
        assert "Ranked #1 of 1 feasible vessels." in ranked[0].reasons

    def test_every_component_has_a_reason(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v1 = _make_vessel("V1", "MV One")
        voyage_results = [_make_voyage_result(v1, route)]
        cost_results = [_make_cost("V1", "MV One", 500_000.0, 6.67)]
        risk_results = [_make_risk("V1", "MV One", 20.0, RiskCategory.LOW)]
        ranked = engine.feasible(engine.rank(voyage_results, cost_results, risk_results, cargo))
        for component in ranked[0].component_scores:
            assert component.reason

    def test_largest_contributor_reason_matches_actual_largest(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v1 = _make_vessel("V1", "MV One")
        voyage_results = [_make_voyage_result(v1, route, deadline_buffer_days=10.0)]
        cost_results = [_make_cost("V1", "MV One", 500_000.0, 6.67)]
        risk_results = [_make_risk("V1", "MV One", 20.0, RiskCategory.LOW)]
        ranked = engine.feasible(engine.rank(voyage_results, cost_results, risk_results, cargo))
        rv = ranked[0]
        largest = max(rv.component_scores, key=lambda c: c.weighted_contribution)
        assert any(largest.name in r for r in rv.reasons)

    def test_excluded_vessel_reason_explains_why(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v = _make_vessel("V1", "MV Infeasible")
        voyage_results = [
            _make_voyage_result(v, route, feasible=False, reasons=["Capacity too small"])
        ]
        ranked = engine.rank(voyage_results, [], [], cargo)
        excluded = engine.excluded(ranked)
        assert "Capacity too small" in excluded[0].reasons
        assert any("feasibility" in r.lower() for r in excluded[0].reasons)

    def test_assumptions_documented(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v1 = _make_vessel("V1", "MV One")
        voyage_results = [_make_voyage_result(v1, route)]
        cost_results = [_make_cost("V1", "MV One", 500_000.0, 6.67)]
        risk_results = [_make_risk("V1", "MV One", 20.0, RiskCategory.LOW)]
        ranked = engine.feasible(engine.rank(voyage_results, cost_results, risk_results, cargo))
        assert len(ranked[0].assumptions) > 0


# ---------------------------------------------------------------------------
# Missing data validation
# ---------------------------------------------------------------------------


class TestMissingDataValidation:
    def test_missing_cost_for_feasible_vessel_raises(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v1 = _make_vessel("V1", "MV One")
        voyage_results = [_make_voyage_result(v1, route)]
        risk_results = [_make_risk("V1", "MV One", 20.0, RiskCategory.LOW)]
        with pytest.raises(ValueError, match="Missing VoyageCostBreakdown"):
            engine.rank(voyage_results, [], risk_results, cargo)

    def test_missing_risk_for_feasible_vessel_raises(
        self, engine: RankingEngine, cargo: Cargo, route: Route
    ) -> None:
        v1 = _make_vessel("V1", "MV One")
        voyage_results = [_make_voyage_result(v1, route)]
        cost_results = [_make_cost("V1", "MV One", 500_000.0, 6.67)]
        with pytest.raises(ValueError, match="Missing RiskAssessmentResult"):
            engine.rank(voyage_results, cost_results, [], cargo)


# ---------------------------------------------------------------------------
# Full pipeline integration (Phase 1 -> 2 -> 3 -> 4 -> 5)
# ---------------------------------------------------------------------------


class TestFullPipelineIntegration:
    def test_matching_to_ranking_pipeline(self) -> None:
        from optimization_engine.data.mock.fixtures import (
            MOCK_VESSELS,
            PARADIP,
            ROUTE_LOOKUP,
            SAMPLE_CARGO,
            SAMPLE_COST_INPUT,
            SHANGHAI,
        )
        from optimization_engine.economics.engine import VoyageEconomicsEngine
        from optimization_engine.matching.engine import MatchingEngine
        from optimization_engine.risk.engine import RiskEngine
        from optimization_engine.voyage.engine import VoyageFeasibilityEngine

        matching_engine = MatchingEngine()
        match_results = matching_engine.match_vessels(SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP)
        feasible_matches = matching_engine.feasible(match_results)

        route = ROUTE_LOOKUP["CNSHA-INPRT"]
        voyage_engine = VoyageFeasibilityEngine()
        voyage_results = voyage_engine.evaluate_all(feasible_matches, route, SAMPLE_CARGO)
        voyage_feasible = [vr for vr in voyage_results if vr.feasible]

        economics_engine = VoyageEconomicsEngine()
        cost_results = [
            economics_engine.calculate(vr, SAMPLE_CARGO, SAMPLE_COST_INPUT) for vr in voyage_feasible
        ]

        risk_engine = RiskEngine()
        risk_results = risk_engine.assess_all(voyage_feasible, SAMPLE_CARGO)

        ranking_engine = RankingEngine()
        ranked = ranking_engine.rank(voyage_results, cost_results, risk_results, SAMPLE_CARGO)

        feasible = ranking_engine.feasible(ranked)
        assert len(feasible) == len(voyage_feasible)

        # Ranks are contiguous starting at 1
        assert [rv.rank for rv in feasible] == list(range(1, len(feasible) + 1))

        for rv in feasible:
            assert isinstance(rv, RankedVessel)
            assert 0.0 <= rv.overall_score <= 100.0
            assert len(rv.component_scores) == 6
            assert rv.raw_metrics is not None
            assert len(rv.reasons) > 0
            assert len(rv.assumptions) > 0

        # Scores are non-increasing by rank (best first)
        scores = [rv.overall_score for rv in feasible]
        assert scores == sorted(scores, reverse=True)
