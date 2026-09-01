"""
Unit tests for individual hard-constraint rules.

Each test verifies both the pass/fail result and the human-readable
rejection reason (where applicable).
"""

from __future__ import annotations

from datetime import date

import pytest

from optimization_engine.domain.models import (
    Cargo,
    Port,
    Vessel,
    VesselStatus,
)
from optimization_engine.rules.constraints import (
    check_availability_window,
    check_beam_compatibility,
    check_capacity,
    check_cargo_compatibility,
    check_draft_compatibility,
    check_loa_compatibility,
    check_status,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_cargo() -> Cargo:
    return Cargo(
        cargo_id="TEST-001",
        cargo_type="iron_ore",
        quantity_mt=75_000.0,
        origin_port="CNSHA",
        destination_port="INPRT",
        required_arrival_date=date(2026, 10, 15),
    )


@pytest.fixture
def destination_port() -> Port:
    return Port(
        port_id="INPRT",
        port_name="Paradip",
        country="India",
        max_draft_m=14.5,
        max_loa_m=300.0,
        max_beam_m=50.0,
    )


def _make_vessel(**overrides) -> Vessel:
    """Helper to create a vessel with sensible defaults, overriding as needed."""
    defaults = dict(
        vessel_id="V-TEST",
        vessel_name="MV Test Vessel",
        imo="IMO9999999",
        mmsi="MMSI999999",
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
    defaults.update(overrides)
    return Vessel(**defaults)


# ---------------------------------------------------------------------------
# 1. Capacity
# ---------------------------------------------------------------------------


class TestCapacity:
    def test_capacity_pass(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(cargo_capacity_mt=85_000.0)
        result = check_capacity(vessel, sample_cargo)
        assert result.passed is True
        assert result.reason is None

    def test_capacity_exact_match(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(cargo_capacity_mt=75_000.0)
        result = check_capacity(vessel, sample_cargo)
        assert result.passed is True

    def test_capacity_fail(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(cargo_capacity_mt=60_000.0)
        result = check_capacity(vessel, sample_cargo)
        assert result.passed is False
        assert result.reason is not None
        assert "15,000" in result.reason  # shortfall amount
        assert "75,000" in result.reason  # requested amount


# ---------------------------------------------------------------------------
# 2. Cargo Compatibility
# ---------------------------------------------------------------------------


class TestCargoCompatibility:
    def test_cargo_compatibility_pass(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(cargo_types_supported=["iron_ore", "coal"])
        result = check_cargo_compatibility(vessel, sample_cargo)
        assert result.passed is True
        assert result.reason is None

    def test_cargo_compatibility_fail(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(cargo_types_supported=["crude_oil", "lpg"])
        result = check_cargo_compatibility(vessel, sample_cargo)
        assert result.passed is False
        assert result.reason is not None
        assert "iron_ore" in result.reason
        assert "crude_oil" in result.reason


# ---------------------------------------------------------------------------
# 3. Availability Window
# ---------------------------------------------------------------------------


class TestAvailabilityWindow:
    def test_availability_window_pass(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(available_from=date(2026, 8, 1))
        result = check_availability_window(vessel, sample_cargo)
        assert result.passed is True
        assert result.reason is None

    def test_availability_window_exact_deadline(self, sample_cargo: Cargo) -> None:
        """Vessel available on exactly the deadline date should pass."""
        vessel = _make_vessel(available_from=date(2026, 10, 15))
        result = check_availability_window(vessel, sample_cargo)
        assert result.passed is True

    def test_availability_window_fail(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(available_from=date(2026, 11, 1))
        result = check_availability_window(vessel, sample_cargo)
        assert result.passed is False
        assert result.reason is not None
        assert "planning window" in result.reason
        assert "2026-11-01" in result.reason


# ---------------------------------------------------------------------------
# 4. Status (Operational Readiness)
# ---------------------------------------------------------------------------


class TestStatus:
    def test_status_available(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(status=VesselStatus.AVAILABLE)
        result = check_status(vessel, sample_cargo)
        assert result.passed is True

    def test_status_en_route(self, sample_cargo: Cargo) -> None:
        """EN_ROUTE is operationally ready — should pass."""
        vessel = _make_vessel(status=VesselStatus.EN_ROUTE)
        result = check_status(vessel, sample_cargo)
        assert result.passed is True

    def test_status_loading(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(status=VesselStatus.LOADING)
        result = check_status(vessel, sample_cargo)
        assert result.passed is True

    def test_status_discharging(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(status=VesselStatus.DISCHARGING)
        result = check_status(vessel, sample_cargo)
        assert result.passed is True

    def test_status_maintenance(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(status=VesselStatus.UNDER_MAINTENANCE)
        result = check_status(vessel, sample_cargo)
        assert result.passed is False
        assert result.reason is not None
        assert "under maintenance" in result.reason

    def test_status_laid_up(self, sample_cargo: Cargo) -> None:
        vessel = _make_vessel(status=VesselStatus.LAID_UP)
        result = check_status(vessel, sample_cargo)
        assert result.passed is False
        assert result.reason is not None
        assert "laid up" in result.reason


# ---------------------------------------------------------------------------
# 5. Static Draft Compatibility
# ---------------------------------------------------------------------------


class TestDraftCompatibility:
    def test_draft_compatibility_pass(self, destination_port: Port) -> None:
        vessel = _make_vessel(draft_m=14.0)
        result = check_draft_compatibility(vessel, destination_port)
        assert result.passed is True
        assert result.reason is None

    def test_draft_compatibility_exact_limit(self, destination_port: Port) -> None:
        vessel = _make_vessel(draft_m=14.5)
        result = check_draft_compatibility(vessel, destination_port)
        assert result.passed is True

    def test_draft_compatibility_fail(self, destination_port: Port) -> None:
        vessel = _make_vessel(draft_m=16.5)
        result = check_draft_compatibility(vessel, destination_port)
        assert result.passed is False
        assert result.reason is not None
        assert "16.5" in result.reason
        assert "Paradip" in result.reason


# ---------------------------------------------------------------------------
# 6. Static LOA Compatibility
# ---------------------------------------------------------------------------


class TestLOACompatibility:
    def test_loa_compatibility_pass(self, destination_port: Port) -> None:
        vessel = _make_vessel(loa_m=250.0)
        result = check_loa_compatibility(vessel, destination_port)
        assert result.passed is True
        assert result.reason is None

    def test_loa_compatibility_fail(self, destination_port: Port) -> None:
        vessel = _make_vessel(loa_m=310.0)
        result = check_loa_compatibility(vessel, destination_port)
        assert result.passed is False
        assert result.reason is not None
        assert "310" in result.reason
        assert "Paradip" in result.reason


# ---------------------------------------------------------------------------
# 7. Static Beam Compatibility
# ---------------------------------------------------------------------------


class TestBeamCompatibility:
    def test_beam_compatibility_pass(self, destination_port: Port) -> None:
        vessel = _make_vessel(beam_m=43.0)
        result = check_beam_compatibility(vessel, destination_port)
        assert result.passed is True
        assert result.reason is None

    def test_beam_compatibility_fail(self, destination_port: Port) -> None:
        vessel = _make_vessel(beam_m=52.0)
        result = check_beam_compatibility(vessel, destination_port)
        assert result.passed is False
        assert result.reason is not None
        assert "52" in result.reason
        assert "Paradip" in result.reason
