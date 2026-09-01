"""
Tests for the what-if scenario simulation engine (Phase 7).

Tests cover:
    - Isolation: baseline inputs are never mutated by simulate()
    - Determinism: identical scenarios produce identical results
    - Every supported scenario type produces the expected direction
      of change
    - Edge cases: missing required scenario parameters raise clearly
    - Absolute/percentage diffs are computed correctly
    - Optional fleet context enables recommendation_changed detection
"""

from __future__ import annotations

from datetime import date

import pytest

from optimization_engine.domain.models import Cargo, Port, Route, Vessel, VesselStatus
from optimization_engine.economics.models import VoyageCostInput
from optimization_engine.risk.models import RiskFactorInput
from optimization_engine.simulation.engine import ScenarioSimulator
from optimization_engine.simulation.models import ScenarioChange, ScenarioType


@pytest.fixture
def simulator() -> ScenarioSimulator:
    return ScenarioSimulator()


@pytest.fixture
def vessel() -> Vessel:
    return Vessel(
        vessel_id="V1", vessel_name="MV Test", imo="IMO1", mmsi="MMSI1",
        vessel_type="bulk_carrier", dwt_mt=95_000.0, cargo_capacity_mt=85_000.0,
        loa_m=250.0, beam_m=43.0, draft_m=14.0, speed_knots=14.5,
        current_location="Singapore", status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 1), cargo_types_supported=["iron_ore"],
    )


@pytest.fixture
def cargo() -> Cargo:
    return Cargo(
        cargo_id="C1", cargo_type="iron_ore", quantity_mt=75_000.0,
        origin_port="CNSHA", destination_port="INPRT",
        required_arrival_date=date(2026, 10, 15), hazardous=False,
    )


@pytest.fixture
def route() -> Route:
    return Route(route_id="R1", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=3_450.0)


@pytest.fixture
def origin_port() -> Port:
    return Port(port_id="CNSHA", port_name="Shanghai", country="China", max_draft_m=20.0, max_loa_m=350.0, max_beam_m=60.0)


@pytest.fixture
def destination_port() -> Port:
    return Port(port_id="INPRT", port_name="Paradip", country="India", max_draft_m=18.0, max_loa_m=300.0, max_beam_m=50.0)


@pytest.fixture
def cost_input() -> VoyageCostInput:
    return VoyageCostInput(
        freight_rate_per_mt=6.0, fuel_price_per_mt=600.0, fuel_consumption_mt_per_day=30.0,
        port_charges_fixed=1_000.0, berth_charge_per_day=500.0, port_days=2.0,
        pilotage_charge=200.0, tug_charge=300.0, cargo_handling_rate_per_mt=0.5,
        expected_waiting_days=0.0, waiting_cost_per_day=1_000.0, expected_demurrage_days=0.0,
        demurrage_rate_per_day=2_000.0, storage_days=0.0, storage_rate_per_day=100.0,
        insurance_rate_per_mt=0.1, maintenance_cost_per_day=300.0, tax_cost=0.0, duty_cost=0.0,
        other_costs=0.0, currency="USD",
    )


# ---------------------------------------------------------------------------
# Isolation: baseline is never mutated
# ---------------------------------------------------------------------------


class TestIsolation:
    def test_cost_input_not_mutated(self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input):
        original_fuel_price = cost_input.fuel_price_per_mt
        simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.FUEL_PRICE_CHANGE, multiplier=1.5),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert cost_input.fuel_price_per_mt == original_fuel_price

    def test_vessel_not_mutated(self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input):
        original_available_from = vessel.available_from
        original_speed = vessel.speed_knots
        original_status = vessel.status
        simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.VESSEL_DELAY, additional_days=5.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.WEATHER_DELAY, additional_days=3.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.VESSEL_UNAVAILABLE),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert vessel.available_from == original_available_from
        assert vessel.speed_knots == original_speed
        assert vessel.status == original_status

    def test_cargo_not_mutated(self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input):
        original_qty = cargo.quantity_mt
        original_deadline = cargo.required_arrival_date
        simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.CARGO_QUANTITY_CHANGE, multiplier=2.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.DEADLINE_CHANGE, deadline_shift_days=-10.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert cargo.quantity_mt == original_qty
        assert cargo.required_arrival_date == original_deadline


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_repeated_runs_produce_identical_result(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        scenario = ScenarioChange(scenario_type=ScenarioType.FUEL_PRICE_CHANGE, multiplier=1.2)
        r1 = simulator.simulate(scenario, vessel, cargo, route, origin_port, destination_port, cost_input)
        r2 = simulator.simulate(scenario, vessel, cargo, route, origin_port, destination_port, cost_input)
        assert r1.scenario.total_cost == r2.scenario.total_cost
        assert r1.baseline.total_cost == r2.baseline.total_cost


# ---------------------------------------------------------------------------
# Each scenario type: correct direction of change
# ---------------------------------------------------------------------------


class TestScenarioDirections:
    def test_fuel_price_increase_raises_cost(self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.FUEL_PRICE_CHANGE, multiplier=1.2),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert r.scenario.total_cost > r.baseline.total_cost

    def test_fuel_price_decrease_lowers_cost(self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.FUEL_PRICE_CHANGE, multiplier=0.8),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert r.scenario.total_cost < r.baseline.total_cost

    def test_freight_rate_increase_raises_cost(self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.FREIGHT_RATE_CHANGE, multiplier=1.1),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert r.scenario.total_cost > r.baseline.total_cost

    def test_vessel_delay_reduces_deadline_buffer_by_same_amount(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.VESSEL_DELAY, additional_days=2.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert (r.baseline.deadline_buffer_days - r.scenario.deadline_buffer_days) == pytest.approx(2.0, abs=0.01)

    def test_weather_delay_reduces_buffer_and_raises_risk(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.WEATHER_DELAY, additional_days=2.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert (r.baseline.deadline_buffer_days - r.scenario.deadline_buffer_days) == pytest.approx(2.0, abs=0.05)
        assert r.scenario.overall_risk_score >= r.baseline.overall_risk_score

    def test_port_waiting_increase_raises_cost_but_not_eta(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.PORT_WAITING_INCREASE, additional_days=3.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert r.scenario.total_cost > r.baseline.total_cost
        assert r.scenario.deadline_buffer_days == pytest.approx(r.baseline.deadline_buffer_days)

    def test_congestion_increase_raises_risk(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.CONGESTION_INCREASE, congestion_delta=30.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
            risk_input=RiskFactorInput(congestion_risk_score=20.0),
        )
        assert r.scenario.overall_risk_score > r.baseline.overall_risk_score

    def test_cargo_quantity_increase_can_flip_feasibility(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.CARGO_QUANTITY_CHANGE, multiplier=1.5),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert r.baseline.feasible is True
        assert r.scenario.feasible is False
        assert r.feasibility_changed is True

    def test_deadline_tightening_can_flip_feasibility(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.DEADLINE_CHANGE, deadline_shift_days=-70.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert r.scenario.feasible is False

    def test_vessel_unavailable_makes_infeasible(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.VESSEL_UNAVAILABLE),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert r.scenario.feasible is False

    def test_alternative_vessel_uses_substitute(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        alt = Vessel(
            vessel_id="V2", vessel_name="MV Alt", imo="IMO2", mmsi="MMSI2",
            vessel_type="bulk_carrier", dwt_mt=100_000.0, cargo_capacity_mt=90_000.0,
            loa_m=260.0, beam_m=44.0, draft_m=13.0, speed_knots=16.0,
            current_location="Singapore", status=VesselStatus.AVAILABLE,
            available_from=date(2026, 8, 1), cargo_types_supported=["iron_ore"],
        )
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.ALTERNATIVE_VESSEL, alternative_vessel=alt),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        # Faster vessel -> more deadline buffer
        assert r.scenario.deadline_buffer_days > r.baseline.deadline_buffer_days

    def test_alternative_route_uses_substitute_distance(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        alt_route = Route(route_id="R2", origin_port_id="CNSHA", destination_port_id="INPRT", distance_nm=1_000.0)
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.ALTERNATIVE_ROUTE, alternative_route=alt_route),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert r.scenario.deadline_buffer_days > r.baseline.deadline_buffer_days


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_missing_multiplier_raises(self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input):
        with pytest.raises(ValueError, match="requires 'multiplier'"):
            simulator.simulate(
                ScenarioChange(scenario_type=ScenarioType.FUEL_PRICE_CHANGE),
                vessel, cargo, route, origin_port, destination_port, cost_input,
            )

    def test_missing_additional_days_raises(self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input):
        with pytest.raises(ValueError, match="requires 'additional_days'"):
            simulator.simulate(
                ScenarioChange(scenario_type=ScenarioType.VESSEL_DELAY),
                vessel, cargo, route, origin_port, destination_port, cost_input,
            )

    def test_missing_alternative_vessel_raises(self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input):
        with pytest.raises(ValueError, match="requires 'alternative_vessel'"):
            simulator.simulate(
                ScenarioChange(scenario_type=ScenarioType.ALTERNATIVE_VESSEL),
                vessel, cargo, route, origin_port, destination_port, cost_input,
            )

    def test_percentage_difference_none_when_baseline_zero(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        zero_cost_input = cost_input.model_copy(update={
            "expected_waiting_days": 0.0, "waiting_cost_per_day": 0.0,
        })
        # waiting_cost baseline is already 0 in the fixture; confirm the diff handles it
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.FUEL_PRICE_CHANGE, multiplier=1.1),
            vessel, cargo, route, origin_port, destination_port, zero_cost_input,
        )
        assert all(d.baseline_value != 0 or d.percentage_difference is None for d in r.metric_diffs)


# ---------------------------------------------------------------------------
# Fleet context: recommendation_changed
# ---------------------------------------------------------------------------


class TestRecommendationChange:
    def test_no_fleet_context_leaves_recommendation_changed_none(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.FUEL_PRICE_CHANGE, multiplier=1.2),
            vessel, cargo, route, origin_port, destination_port, cost_input,
        )
        assert r.recommendation_changed is None

    def test_fleet_context_detects_recommendation_change(
        self, simulator, vessel, cargo, route, origin_port, destination_port, cost_input
    ):
        from datetime import datetime

        from optimization_engine.domain.models import VoyageFeasibilityResult
        from optimization_engine.economics.models import VoyageCostBreakdown
        from optimization_engine.risk.models import RiskAssessmentResult, RiskCategory, RiskFactorScore

        # A second vessel, cheaper, that should overtake V1 once V1's fuel cost spikes.
        other_vessel = Vessel(
            vessel_id="V2", vessel_name="MV Cheap", imo="IMO2", mmsi="MMSI2",
            vessel_type="bulk_carrier", dwt_mt=90_000.0, cargo_capacity_mt=85_000.0,
            loa_m=250.0, beam_m=43.0, draft_m=14.0, speed_knots=14.5,
            current_location="Singapore", status=VesselStatus.AVAILABLE,
            available_from=date(2026, 8, 1), cargo_types_supported=["iron_ore"],
        )
        other_voyage = VoyageFeasibilityResult(
            vessel=other_vessel, route=route,
            estimated_departure=datetime(2026, 8, 1, 0, 0), sailing_hours=237.93, sailing_days=9.91,
            estimated_arrival=datetime(2026, 8, 10, 21, 56), required_arrival=date(2026, 10, 15),
            # NOTE: deliberately matches vessel's own baseline buffer exactly.
            # Batch-relative ranking (Phase 5) fully amplifies even a tiny
            # buffer difference to a 100/0 split across just 2 candidates,
            # which would otherwise swamp the cost signal this test targets.
            deadline_buffer_days=66.08619532247685, deadline_feasible=True, phase1_feasible=True,
            feasible=True, reasons=[], assumptions=["mock"],
        )
        other_cost = VoyageCostBreakdown(
            vessel_name="MV Cheap", vessel_id="V2", route_id="R1",
            charter_cost=300_000.0, fuel_consumed_mt=300.0, fuel_cost=100_000.0,
            port_cost=1_000.0, berth_cost=1_000.0, pilotage_cost=200.0, tug_cost=300.0,
            cargo_handling_cost=500.0, waiting_cost=0.0, demurrage_cost=0.0, storage_cost=0.0,
            insurance_cost=500.0, maintenance_cost=300.0, tax_cost=0.0, duty_cost=0.0, other_cost=0.0,
            total_cost=690_000.0, cost_per_mt=9.2, currency="USD", assumptions=["mock"],
        )
        other_risk = RiskAssessmentResult(
            vessel_id="V2", vessel_name="MV Cheap", cargo_id="C1", route_id="R1",
            # Matches V1's own baseline risk score exactly, so risk ties too —
            # isolating cost as the only varying ranking dimension in this test.
            overall_risk_score=14.0, risk_category=RiskCategory.LOW,
            factor_scores=[RiskFactorScore(name="weather", raw_score=14.0, weight=1.0, weighted_contribution=14.0, reason="mock")],
            reasons=["mock"], assumptions=["mock"],
        )

        # Baseline: V1 (~679k) should beat V2 (690k). Scenario: spike V1's fuel
        # price hard enough that V2 becomes cheaper.
        r = simulator.simulate(
            ScenarioChange(scenario_type=ScenarioType.FUEL_PRICE_CHANGE, multiplier=3.0),
            vessel, cargo, route, origin_port, destination_port, cost_input,
            other_voyage_results=[other_voyage],
            other_cost_results=[other_cost],
            other_risk_results=[other_risk],
        )
        assert r.recommendation_changed is True
        assert r.baseline_top_vessel_id == "V1"
        assert r.scenario_top_vessel_id == "V2"
