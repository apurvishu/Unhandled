"""
Tests for voyage economics (Phase 3).

Tests cover:
    - Individual cost-calculation functions
    - Total cost = sum of components
    - Cost per MT
    - Input validation (zero cargo quantity)
    - Rate sensitivity (changing fuel price, sailing days, cargo qty)
    - Zero optional costs handled correctly
    - Assumptions and metadata
    - Full pipeline integration (Phase 1 → Phase 2 → Phase 3)
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from optimization_engine.domain.models import (
    Cargo,
    Route,
    Vessel,
    VesselStatus,
    VoyageFeasibilityResult,
)
from optimization_engine.economics.calculations import (
    calculate_berth_cost,
    calculate_cargo_handling_cost,
    calculate_charter_cost,
    calculate_cost_per_mt,
    calculate_demurrage_cost,
    calculate_fuel_consumption,
    calculate_fuel_cost,
    calculate_insurance_cost,
    calculate_maintenance_cost,
    calculate_storage_cost,
    calculate_waiting_cost,
)
from optimization_engine.economics.engine import VoyageEconomicsEngine
from optimization_engine.economics.models import VoyageCostInput


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_cost_input(**overrides) -> VoyageCostInput:
    """Create a VoyageCostInput with sensible demo defaults."""
    defaults = dict(
        freight_rate_per_mt=10.0,
        fuel_price_per_mt=600.0,
        fuel_consumption_mt_per_day=35.0,
        port_charges_fixed=25_000.0,
        berth_charge_per_day=2_000.0,
        port_days=3.0,
        pilotage_charge=5_000.0,
        tug_charge=8_000.0,
        cargo_handling_rate_per_mt=4.50,
        expected_waiting_days=1.5,
        waiting_cost_per_day=15_000.0,
        expected_demurrage_days=0.0,
        demurrage_rate_per_day=20_000.0,
        storage_days=0.0,
        storage_rate_per_day=500.0,
        insurance_rate_per_mt=1.20,
        maintenance_cost_per_day=6_000.0,
        tax_cost=0.0,
        duty_cost=0.0,
        other_costs=5_000.0,
        currency="USD",
    )
    defaults.update(overrides)
    return VoyageCostInput(**defaults)


def _make_voyage_result(**overrides) -> VoyageFeasibilityResult:
    """Create a mock VoyageFeasibilityResult for economics testing."""
    vessel = Vessel(
        vessel_id="V-ECON",
        vessel_name="MV Economics Test",
        imo="IMO6666666",
        mmsi="MMSI666666",
        vessel_type="bulk_carrier",
        dwt_mt=100_000.0,
        cargo_capacity_mt=85_000.0,
        loa_m=250.0,
        beam_m=43.0,
        draft_m=14.0,
        speed_knots=14.5,
        current_location="Test Port",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 1),
        cargo_types_supported=["iron_ore", "coal"],
    )
    route = Route(
        route_id="CNSHA-INPRT",
        origin_port_id="CNSHA",
        destination_port_id="INPRT",
        distance_nm=3_450.0,
    )
    defaults = dict(
        vessel=vessel,
        route=route,
        estimated_departure=datetime(2026, 8, 1, 0, 0),
        sailing_hours=237.93,
        sailing_days=9.91,
        estimated_arrival=datetime(2026, 8, 10, 21, 56),
        required_arrival=date(2026, 10, 15),
        deadline_buffer_days=65.09,
        deadline_feasible=True,
        phase1_feasible=True,
        feasible=True,
        reasons=[],
        assumptions=["mock"],
    )
    defaults.update(overrides)
    return VoyageFeasibilityResult(**defaults)


@pytest.fixture
def engine() -> VoyageEconomicsEngine:
    return VoyageEconomicsEngine()


@pytest.fixture
def sample_cargo() -> Cargo:
    return Cargo(
        cargo_id="TEST-EC-001",
        cargo_type="iron_ore",
        quantity_mt=75_000.0,
        origin_port="CNSHA",
        destination_port="INPRT",
        required_arrival_date=date(2026, 10, 15),
    )


@pytest.fixture
def cost_input() -> VoyageCostInput:
    return _make_cost_input()


@pytest.fixture
def voyage_result() -> VoyageFeasibilityResult:
    return _make_voyage_result()


# ---------------------------------------------------------------------------
# 1-2. Fuel calculations
# ---------------------------------------------------------------------------


class TestFuelCalculations:
    def test_fuel_consumption(self) -> None:
        """35 MT/day × 10 days = 350 MT."""
        result = calculate_fuel_consumption(35.0, 10.0)
        assert result == pytest.approx(350.0)

    def test_fuel_cost(self) -> None:
        """350 MT × $600/MT = $210,000."""
        result = calculate_fuel_cost(350.0, 600.0)
        assert result == pytest.approx(210_000.0)

    def test_fuel_consumption_fractional_days(self) -> None:
        """35 MT/day × 9.91 days = 346.85 MT."""
        result = calculate_fuel_consumption(35.0, 9.91)
        assert result == pytest.approx(346.85)


# ---------------------------------------------------------------------------
# 3. Charter/freight cost
# ---------------------------------------------------------------------------


class TestCharterCost:
    def test_charter_cost(self) -> None:
        """$10/MT × 75,000 MT = $750,000."""
        result = calculate_charter_cost(10.0, 75_000.0)
        assert result == pytest.approx(750_000.0)


# ---------------------------------------------------------------------------
# 4-7. Port costs
# ---------------------------------------------------------------------------


class TestPortCosts:
    def test_berth_cost(self) -> None:
        """$2,000/day × 3 days = $6,000."""
        result = calculate_berth_cost(2_000.0, 3.0)
        assert result == pytest.approx(6_000.0)

    def test_cargo_handling_cost(self) -> None:
        """$4.50/MT × 75,000 MT = $337,500."""
        result = calculate_cargo_handling_cost(4.50, 75_000.0)
        assert result == pytest.approx(337_500.0)


# ---------------------------------------------------------------------------
# 8-9. Waiting / Demurrage
# ---------------------------------------------------------------------------


class TestWaitingDemurrage:
    def test_waiting_cost(self) -> None:
        """$15,000/day × 1.5 days = $22,500."""
        result = calculate_waiting_cost(15_000.0, 1.5)
        assert result == pytest.approx(22_500.0)

    def test_demurrage_cost(self) -> None:
        """$20,000/day × 2 days = $40,000."""
        result = calculate_demurrage_cost(20_000.0, 2.0)
        assert result == pytest.approx(40_000.0)

    def test_zero_demurrage(self) -> None:
        """Zero demurrage days → zero cost."""
        result = calculate_demurrage_cost(20_000.0, 0.0)
        assert result == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 10. Storage
# ---------------------------------------------------------------------------


class TestStorageCost:
    def test_storage_cost(self) -> None:
        """$500/day × 5 days = $2,500."""
        result = calculate_storage_cost(500.0, 5.0)
        assert result == pytest.approx(2_500.0)

    def test_zero_storage(self) -> None:
        result = calculate_storage_cost(500.0, 0.0)
        assert result == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 10. Insurance
# ---------------------------------------------------------------------------


class TestInsuranceCost:
    def test_insurance_cost(self) -> None:
        """$1.20/MT × 75,000 MT = $90,000."""
        result = calculate_insurance_cost(1.20, 75_000.0)
        assert result == pytest.approx(90_000.0)


# ---------------------------------------------------------------------------
# 11. Maintenance
# ---------------------------------------------------------------------------


class TestMaintenanceCost:
    def test_maintenance_cost(self) -> None:
        """$6,000/day × 14.41 days = $86,460."""
        result = calculate_maintenance_cost(6_000.0, 14.41)
        assert result == pytest.approx(86_460.0)


# ---------------------------------------------------------------------------
# 12-13. Total cost and cost per MT
# ---------------------------------------------------------------------------


class TestTotalCost:
    def test_total_cost_is_sum_of_components(
        self,
        engine: VoyageEconomicsEngine,
        voyage_result: VoyageFeasibilityResult,
        sample_cargo: Cargo,
        cost_input: VoyageCostInput,
    ) -> None:
        """Total must equal the arithmetic sum of all individual components."""
        result = engine.calculate(voyage_result, sample_cargo, cost_input)

        expected_total = (
            result.charter_cost
            + result.fuel_cost
            + result.port_cost
            + result.berth_cost
            + result.pilotage_cost
            + result.tug_cost
            + result.cargo_handling_cost
            + result.waiting_cost
            + result.demurrage_cost
            + result.storage_cost
            + result.insurance_cost
            + result.maintenance_cost
            + result.tax_cost
            + result.duty_cost
            + result.other_cost
        )
        assert result.total_cost == pytest.approx(expected_total)

    def test_cost_per_mt(
        self,
        engine: VoyageEconomicsEngine,
        voyage_result: VoyageFeasibilityResult,
        sample_cargo: Cargo,
        cost_input: VoyageCostInput,
    ) -> None:
        """cost_per_mt = total_cost / cargo_quantity_mt."""
        result = engine.calculate(voyage_result, sample_cargo, cost_input)

        assert result.cost_per_mt == pytest.approx(
            result.total_cost / sample_cargo.quantity_mt
        )


# ---------------------------------------------------------------------------
# 14. Zero cargo quantity
# ---------------------------------------------------------------------------


class TestZeroCargoRejected:
    def test_zero_cargo_quantity_rejected(self) -> None:
        """Zero cargo quantity should raise ValueError."""
        with pytest.raises(ValueError, match="cargo_quantity_mt must be > 0"):
            calculate_cost_per_mt(100_000.0, 0.0)

    def test_negative_cargo_quantity_rejected(self) -> None:
        with pytest.raises(ValueError, match="cargo_quantity_mt must be > 0"):
            calculate_cost_per_mt(100_000.0, -1000.0)


# ---------------------------------------------------------------------------
# 16-18. Rate sensitivity
# ---------------------------------------------------------------------------


class TestRateSensitivity:
    def test_changing_fuel_price_changes_fuel_cost(
        self,
        engine: VoyageEconomicsEngine,
        voyage_result: VoyageFeasibilityResult,
        sample_cargo: Cargo,
    ) -> None:
        """Higher fuel price → higher fuel cost, same fuel consumption."""
        low_fuel = _make_cost_input(fuel_price_per_mt=400.0)
        high_fuel = _make_cost_input(fuel_price_per_mt=800.0)

        result_low = engine.calculate(voyage_result, sample_cargo, low_fuel)
        result_high = engine.calculate(voyage_result, sample_cargo, high_fuel)

        assert result_low.fuel_consumed_mt == pytest.approx(result_high.fuel_consumed_mt)
        assert result_high.fuel_cost > result_low.fuel_cost
        assert result_high.fuel_cost == pytest.approx(result_low.fuel_cost * 2.0)

    def test_changing_sailing_days_changes_fuel_consumption(
        self,
        engine: VoyageEconomicsEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Longer voyage → more fuel consumed."""
        short_voyage = _make_voyage_result(sailing_days=5.0, sailing_hours=120.0)
        long_voyage = _make_voyage_result(sailing_days=15.0, sailing_hours=360.0)
        ci = _make_cost_input()

        result_short = engine.calculate(short_voyage, sample_cargo, ci)
        result_long = engine.calculate(long_voyage, sample_cargo, ci)

        assert result_long.fuel_consumed_mt > result_short.fuel_consumed_mt
        assert result_long.fuel_consumed_mt == pytest.approx(
            result_short.fuel_consumed_mt * 3.0
        )

    def test_changing_cargo_quantity_changes_per_ton_cost(
        self,
        engine: VoyageEconomicsEngine,
        voyage_result: VoyageFeasibilityResult,
    ) -> None:
        """Larger cargo → lower cost per MT (fixed costs spread over more tonnes)."""
        small_cargo = Cargo(
            cargo_id="T-SMALL",
            cargo_type="iron_ore",
            quantity_mt=50_000.0,
            origin_port="CNSHA",
            destination_port="INPRT",
            required_arrival_date=date(2026, 10, 15),
        )
        large_cargo = Cargo(
            cargo_id="T-LARGE",
            cargo_type="iron_ore",
            quantity_mt=150_000.0,
            origin_port="CNSHA",
            destination_port="INPRT",
            required_arrival_date=date(2026, 10, 15),
        )
        ci = _make_cost_input()

        result_small = engine.calculate(voyage_result, small_cargo, ci)
        result_large = engine.calculate(voyage_result, large_cargo, ci)

        # Fixed costs (port, pilotage, tug, fuel, maintenance) are the same
        assert result_small.fuel_cost == pytest.approx(result_large.fuel_cost)
        # Cost per MT is lower for larger cargo
        assert result_large.cost_per_mt < result_small.cost_per_mt


# ---------------------------------------------------------------------------
# 19. Zero optional costs
# ---------------------------------------------------------------------------


class TestZeroOptionalCosts:
    def test_all_optional_costs_zero(
        self,
        engine: VoyageEconomicsEngine,
        voyage_result: VoyageFeasibilityResult,
        sample_cargo: Cargo,
    ) -> None:
        """Only mandatory costs should contribute when all optional costs are zero."""
        minimal = VoyageCostInput(
            freight_rate_per_mt=10.0,
            fuel_price_per_mt=600.0,
            fuel_consumption_mt_per_day=35.0,
        )

        result = engine.calculate(voyage_result, sample_cargo, minimal)

        assert result.port_cost == 0.0
        assert result.berth_cost == 0.0
        assert result.pilotage_cost == 0.0
        assert result.tug_cost == 0.0
        assert result.cargo_handling_cost == 0.0
        assert result.waiting_cost == 0.0
        assert result.demurrage_cost == 0.0
        assert result.storage_cost == 0.0
        assert result.insurance_cost == 0.0
        assert result.maintenance_cost == 0.0
        assert result.tax_cost == 0.0
        assert result.duty_cost == 0.0
        assert result.other_cost == 0.0
        # Total = charter + fuel only
        expected = result.charter_cost + result.fuel_cost
        assert result.total_cost == pytest.approx(expected)


# ---------------------------------------------------------------------------
# 20-21. Assumptions and metadata
# ---------------------------------------------------------------------------


class TestCostMetadata:
    def test_assumptions_included(
        self,
        engine: VoyageEconomicsEngine,
        voyage_result: VoyageFeasibilityResult,
        sample_cargo: Cargo,
        cost_input: VoyageCostInput,
    ) -> None:
        """Result should include documented assumptions."""
        result = engine.calculate(voyage_result, sample_cargo, cost_input)

        assert len(result.assumptions) > 0
        text = " ".join(result.assumptions).lower()
        assert "mock" in text or "demo" in text

    def test_evaluated_at_populated(
        self,
        engine: VoyageEconomicsEngine,
        voyage_result: VoyageFeasibilityResult,
        sample_cargo: Cargo,
        cost_input: VoyageCostInput,
    ) -> None:
        """Result should have an evaluated_at timestamp."""
        result = engine.calculate(voyage_result, sample_cargo, cost_input)
        assert result.evaluated_at is not None

    def test_currency_propagated(
        self,
        engine: VoyageEconomicsEngine,
        voyage_result: VoyageFeasibilityResult,
        sample_cargo: Cargo,
    ) -> None:
        """Currency from cost input should propagate to result."""
        ci = _make_cost_input(currency="INR")
        result = engine.calculate(voyage_result, sample_cargo, ci)
        assert result.currency == "INR"


# ---------------------------------------------------------------------------
# Full pipeline integration: Phase 1 → Phase 2 → Phase 3
# ---------------------------------------------------------------------------


class TestFullPipelineIntegration:
    def test_phase1_to_phase2_to_phase3(self) -> None:
        """End-to-end: match → voyage feasibility → economics."""
        from optimization_engine.data.mock.fixtures import (
            MOCK_VESSELS,
            PARADIP,
            ROUTE_LOOKUP,
            SAMPLE_CARGO,
            SAMPLE_COST_INPUT,
            SHANGHAI,
        )
        from optimization_engine.matching.engine import MatchingEngine
        from optimization_engine.voyage.engine import VoyageFeasibilityEngine

        # Phase 1
        matching_engine = MatchingEngine()
        match_results = matching_engine.match_vessels(
            SAMPLE_CARGO, MOCK_VESSELS, SHANGHAI, PARADIP
        )
        feasible_matches = matching_engine.feasible(match_results)
        assert len(feasible_matches) > 0

        # Phase 2
        route = ROUTE_LOOKUP["CNSHA-INPRT"]
        voyage_engine = VoyageFeasibilityEngine()
        voyage_results = voyage_engine.evaluate_all(
            feasible_matches, route, SAMPLE_CARGO
        )
        voyage_feasible = [vr for vr in voyage_results if vr.feasible]
        assert len(voyage_feasible) > 0

        # Phase 3
        economics_engine = VoyageEconomicsEngine()
        cost_results = economics_engine.calculate_all(
            voyage_feasible, SAMPLE_CARGO, SAMPLE_COST_INPUT
        )

        assert len(cost_results) == len(voyage_feasible)
        for cr in cost_results:
            assert cr.total_cost > 0
            assert cr.cost_per_mt > 0
            assert cr.fuel_consumed_mt > 0
            assert cr.charter_cost > 0
            assert cr.currency == "USD"
            assert len(cr.assumptions) > 0
