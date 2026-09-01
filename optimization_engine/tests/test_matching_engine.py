"""
Integration tests for the MatchingEngine.

Tests assert **per-vessel outcomes** (by vessel name/id), not aggregate
counts like "6 feasible / 14 rejected".  This keeps tests stable as
mock data evolves.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from optimization_engine.domain.models import (
    Cargo,
    Port,
    Vessel,
    VesselStatus,
)
from optimization_engine.matching.engine import MatchingEngine


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> MatchingEngine:
    return MatchingEngine()


@pytest.fixture
def sample_cargo() -> Cargo:
    return Cargo(
        cargo_id="TEST-INT-001",
        cargo_type="iron_ore",
        quantity_mt=75_000.0,
        origin_port="CNSHA",
        destination_port="INPRT",
        required_arrival_date=date(2026, 10, 15),
    )


@pytest.fixture
def origin_port() -> Port:
    return Port(
        port_id="CNSHA",
        port_name="Shanghai",
        country="China",
        max_draft_m=16.0,
        max_loa_m=350.0,
        max_beam_m=55.0,
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
    """Helper to create a vessel with sensible defaults."""
    defaults = dict(
        vessel_id="V-INT-TEST",
        vessel_name="MV Integration Test",
        imo="IMO8888888",
        mmsi="MMSI888888",
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
# Tests
# ---------------------------------------------------------------------------


class TestKnownValidVessel:
    """A specific known-good vessel should be feasible with all checks passing."""

    def test_known_valid_vessel_is_feasible(
        self,
        engine: MatchingEngine,
        sample_cargo: Cargo,
        origin_port: Port,
        destination_port: Port,
    ) -> None:
        valid_vessel = _make_vessel(
            vessel_id="V-VALID",
            vessel_name="MV Known Good",
            cargo_capacity_mt=90_000.0,
            draft_m=13.0,
            loa_m=240.0,
            beam_m=42.0,
        )

        results = engine.match_vessels(
            sample_cargo, [valid_vessel], origin_port, destination_port
        )

        assert len(results) == 1
        result = results[0]
        assert result.feasible is True
        assert result.rejection_reasons == []
        assert all(c.passed for c in result.checks)


class TestKnownRejectedVessel:
    """A specific known-bad vessel should be rejected with the expected reason."""

    def test_known_rejected_vessel_has_reasons(
        self,
        engine: MatchingEngine,
        sample_cargo: Cargo,
        origin_port: Port,
        destination_port: Port,
    ) -> None:
        tanker = _make_vessel(
            vessel_id="V-TANKER",
            vessel_name="MV Petro Test",
            cargo_types_supported=["crude_oil", "fuel_oil"],
        )

        results = engine.match_vessels(
            sample_cargo, [tanker], origin_port, destination_port
        )

        assert len(results) == 1
        result = results[0]
        assert result.feasible is False
        assert any("iron_ore" in r for r in result.rejection_reasons)


class TestNoFeasibleVessels:
    """When all vessels are unfit, zero should be feasible."""

    def test_no_feasible_when_all_unfit(
        self,
        engine: MatchingEngine,
        sample_cargo: Cargo,
        origin_port: Port,
        destination_port: Port,
    ) -> None:
        unfit_vessels = [
            _make_vessel(
                vessel_id="V-SMALL",
                vessel_name="MV Too Small",
                cargo_capacity_mt=30_000.0,
            ),
            _make_vessel(
                vessel_id="V-WRONG-TYPE",
                vessel_name="MV Wrong Type",
                cargo_types_supported=["lpg"],
            ),
            _make_vessel(
                vessel_id="V-MAINT",
                vessel_name="MV In Drydock",
                status=VesselStatus.UNDER_MAINTENANCE,
            ),
        ]

        results = engine.match_vessels(
            sample_cargo, unfit_vessels, origin_port, destination_port
        )

        feasible = engine.feasible(results)
        rejected = engine.rejected(results)

        assert len(feasible) == 0
        assert len(rejected) == 3
        for r in rejected:
            assert len(r.rejection_reasons) >= 1


class TestRejectionReasonsAreHumanReadable:
    """Rejection reasons should contain contextual numbers/names, not just 'failed'."""

    def test_rejection_reasons_are_human_readable(
        self,
        engine: MatchingEngine,
        sample_cargo: Cargo,
        origin_port: Port,
        destination_port: Port,
    ) -> None:
        small_vessel = _make_vessel(
            vessel_id="V-HR",
            vessel_name="MV Human Readable",
            cargo_capacity_mt=50_000.0,
        )

        results = engine.match_vessels(
            sample_cargo, [small_vessel], origin_port, destination_port
        )

        result = results[0]
        assert result.feasible is False
        # The reason should contain actual numbers, not just "failed"
        reason = result.rejection_reasons[0]
        assert "50,000" in reason or "25,000" in reason or "75,000" in reason


class TestMultipleFailuresCollected:
    """A vessel failing 2+ checks should have ALL reasons listed."""

    def test_multiple_failures_collected(
        self,
        engine: MatchingEngine,
        sample_cargo: Cargo,
        origin_port: Port,
        destination_port: Port,
    ) -> None:
        # Fails on: capacity (45,000 < 75,000) AND draft (15.5 > 14.5)
        multi_fail_vessel = _make_vessel(
            vessel_id="V-MULTI",
            vessel_name="MV Multi Fail",
            cargo_capacity_mt=45_000.0,
            draft_m=15.5,
        )

        results = engine.match_vessels(
            sample_cargo, [multi_fail_vessel], origin_port, destination_port
        )

        result = results[0]
        assert result.feasible is False
        assert len(result.rejection_reasons) >= 2
        # Verify both failure types are represented
        reasons_text = " ".join(result.rejection_reasons).lower()
        assert "capacity" in reasons_text or "mt" in reasons_text.lower()
        assert "draft" in reasons_text


class TestEvaluatedAtTimestamp:
    """Every MatchResult should have a populated evaluated_at timestamp."""

    def test_evaluated_at_is_populated(
        self,
        engine: MatchingEngine,
        sample_cargo: Cargo,
        origin_port: Port,
        destination_port: Port,
    ) -> None:
        vessel = _make_vessel(vessel_id="V-TS", vessel_name="MV Timestamp Test")
        before = datetime.now(UTC)

        results = engine.match_vessels(
            sample_cargo, [vessel], origin_port, destination_port
        )

        after = datetime.now(UTC)
        result = results[0]
        assert result.evaluated_at is not None
        assert before <= result.evaluated_at <= after


class TestMixedFeasibleAndRejected:
    """A mixed set of vessels should correctly separate feasible from rejected."""

    def test_mixed_set_per_vessel_outcome(
        self,
        engine: MatchingEngine,
        sample_cargo: Cargo,
        origin_port: Port,
        destination_port: Port,
    ) -> None:
        good_vessel = _make_vessel(
            vessel_id="V-GOOD",
            vessel_name="MV Good Vessel",
            cargo_capacity_mt=85_000.0,
        )
        bad_vessel = _make_vessel(
            vessel_id="V-BAD",
            vessel_name="MV Bad Vessel",
            cargo_capacity_mt=30_000.0,
        )

        results = engine.match_vessels(
            sample_cargo,
            [good_vessel, bad_vessel],
            origin_port,
            destination_port,
        )

        result_by_id = {r.vessel.vessel_id: r for r in results}
        assert result_by_id["V-GOOD"].feasible is True
        assert result_by_id["V-BAD"].feasible is False
