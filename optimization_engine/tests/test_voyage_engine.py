"""
Integration tests for VoyageFeasibilityEngine.

Tests cover:
    - Correct ETA calculation with sub-day precision
    - Deadline feasibility (before / exactly / after)
    - Deadline buffer (positive / zero / negative / fractional)
    - Phase 1 + Phase 2 combined feasibility logic
    - Route validation
    - Input validation
    - Date edge cases (arrival noon on deadline day vs 00:01 next day)
    - Assumptions and timestamp population

Tests assert per-vessel outcomes, not aggregate counts.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from optimization_engine.domain.models import (
    Cargo,
    ConstraintCheck,
    MatchResult,
    Route,
    Vessel,
    VesselStatus,
)
from optimization_engine.voyage.engine import VoyageFeasibilityEngine


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> VoyageFeasibilityEngine:
    return VoyageFeasibilityEngine()


@pytest.fixture
def sample_route() -> Route:
    return Route(
        route_id="CNSHA-INPRT",
        origin_port_id="CNSHA",
        destination_port_id="INPRT",
        distance_nm=3_450.0,
    )


@pytest.fixture
def sample_cargo() -> Cargo:
    return Cargo(
        cargo_id="TEST-V2-001",
        cargo_type="iron_ore",
        quantity_mt=75_000.0,
        origin_port="CNSHA",
        destination_port="INPRT",
        required_arrival_date=date(2026, 10, 15),
    )


def _make_vessel(**overrides) -> Vessel:
    """Helper to create a vessel with sensible defaults."""
    defaults = dict(
        vessel_id="V-VF-TEST",
        vessel_name="MV Voyage Test",
        imo="IMO7777777",
        mmsi="MMSI777777",
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


def _make_feasible_match(**vessel_overrides) -> MatchResult:
    """Create a Phase 1-feasible MatchResult."""
    vessel = _make_vessel(**vessel_overrides)
    return MatchResult(
        vessel=vessel,
        feasible=True,
        checks=[
            ConstraintCheck(name="capacity", passed=True),
            ConstraintCheck(name="cargo_compatibility", passed=True),
            ConstraintCheck(name="availability_window", passed=True),
            ConstraintCheck(name="status", passed=True),
            ConstraintCheck(name="draft_compatibility", passed=True),
            ConstraintCheck(name="loa_compatibility", passed=True),
            ConstraintCheck(name="beam_compatibility", passed=True),
        ],
        rejection_reasons=[],
    )


def _make_rejected_match(reasons: list[str], **vessel_overrides) -> MatchResult:
    """Create a Phase 1-rejected MatchResult with given reasons."""
    vessel = _make_vessel(**vessel_overrides)
    return MatchResult(
        vessel=vessel,
        feasible=False,
        checks=[
            ConstraintCheck(name="capacity", passed=False, reason=reasons[0]),
        ],
        rejection_reasons=reasons,
    )


# ---------------------------------------------------------------------------
# Estimated departure
# ---------------------------------------------------------------------------


class TestEstimatedDeparture:
    def test_departure_equals_available_from_at_midnight(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Estimated departure should be vessel.available_from at 00:00."""
        match = _make_feasible_match(available_from=date(2026, 9, 5))

        result = engine.evaluate(match, sample_route, sample_cargo)

        expected_departure = datetime(2026, 9, 5, 0, 0, 0)
        assert result.estimated_departure == expected_departure


# ---------------------------------------------------------------------------
# Sailing time
# ---------------------------------------------------------------------------


class TestSailingTime:
    def test_correct_sailing_hours(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """3450 nm / 14.5 kn = 237.931... hours."""
        match = _make_feasible_match(speed_knots=14.5)

        result = engine.evaluate(match, sample_route, sample_cargo)

        expected_hours = 3450.0 / 14.5
        assert result.sailing_hours == pytest.approx(expected_hours)

    def test_correct_sailing_days(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """sailing_days = sailing_hours / 24."""
        match = _make_feasible_match(speed_knots=14.5)

        result = engine.evaluate(match, sample_route, sample_cargo)

        expected_days = (3450.0 / 14.5) / 24.0
        assert result.sailing_days == pytest.approx(expected_days)


# ---------------------------------------------------------------------------
# Estimated arrival (sub-day precision)
# ---------------------------------------------------------------------------


class TestEstimatedArrival:
    def test_correct_arrival_with_fractional_hours(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Arrival = departure + sailing_hours as timedelta."""
        match = _make_feasible_match(
            available_from=date(2026, 8, 1),
            speed_knots=14.5,
        )

        result = engine.evaluate(match, sample_route, sample_cargo)

        sailing_hours = 3450.0 / 14.5
        expected_arrival = datetime(2026, 8, 1, 0, 0) + timedelta(
            hours=sailing_hours
        )
        # Compare within 1 second tolerance
        diff = abs((result.estimated_arrival - expected_arrival).total_seconds())
        assert diff < 1.0


# ---------------------------------------------------------------------------
# Deadline feasibility
# ---------------------------------------------------------------------------


class TestDeadlineFeasibility:
    def test_arrival_before_deadline_is_feasible(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Vessel arriving well before deadline → deadline_feasible=True."""
        match = _make_feasible_match(available_from=date(2026, 8, 1))

        result = engine.evaluate(match, sample_route, sample_cargo)

        assert result.deadline_feasible is True

    def test_arrival_on_deadline_day_at_noon_is_feasible(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Arrival at noon on the required arrival date → FEASIBLE.

        This is the critical edge case: the deadline is the END of the
        required arrival date (23:59:59), so noon arrival is well within
        the window.
        """
        # Engineer: departure Oct 1 00:00, speed 12 kn, distance 4176 nm
        # → 4176/12 = 348 hours = 14.5 days
        # → arrival = Oct 15 12:00
        # → deadline = Oct 15 23:59:59
        # → 12:00 <= 23:59:59 → FEASIBLE
        route = Route(
            route_id="R-EDGE",
            origin_port_id="CNSHA",
            destination_port_id="INPRT",
            distance_nm=4176.0,
        )
        match = _make_feasible_match(
            available_from=date(2026, 10, 1),
            speed_knots=12.0,
        )

        result = engine.evaluate(match, route, sample_cargo)

        assert result.deadline_feasible is True
        assert result.feasible is True
        # Verify arrival is indeed Oct 15 12:00
        assert result.estimated_arrival.month == 10
        assert result.estimated_arrival.day == 15
        assert result.estimated_arrival.hour == 12

    def test_arrival_after_deadline_day_is_infeasible(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Arrival at midnight after the deadline day → INFEASIBLE.

        Departure Oct 1 00:00, speed 12 kn, distance 4320 nm
        → 4320/12 = 360 hours = 15.0 days
        → arrival = Oct 16 00:00
        → deadline = Oct 15 23:59:59
        → 00:00 Oct 16 > 23:59:59 Oct 15 → INFEASIBLE
        """
        route = Route(
            route_id="R-EDGE",
            origin_port_id="CNSHA",
            destination_port_id="INPRT",
            distance_nm=4320.0,
        )
        match = _make_feasible_match(
            available_from=date(2026, 10, 1),
            speed_knots=12.0,
        )

        result = engine.evaluate(match, route, sample_cargo)

        assert result.deadline_feasible is False
        assert result.feasible is False
        assert result.estimated_arrival.day == 16
        assert len(result.reasons) >= 1
        assert any("deadline" in r.lower() for r in result.reasons)

    def test_arrival_exactly_at_end_of_deadline_day(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Arrival very close to 23:59:59 on deadline day → FEASIBLE.

        Verify the <= comparison works at the boundary.
        """
        # 14 days 23 hours = 359 hours → arrival Oct 15 23:00
        route = Route(
            route_id="R-EDGE",
            origin_port_id="CNSHA",
            destination_port_id="INPRT",
            distance_nm=4308.0,  # 4308 / 12 = 359 hours = 14d 23h
        )
        match = _make_feasible_match(
            available_from=date(2026, 10, 1),
            speed_knots=12.0,
        )

        result = engine.evaluate(match, route, sample_cargo)

        assert result.deadline_feasible is True
        assert result.estimated_arrival.day == 15
        assert result.estimated_arrival.hour == 23


# ---------------------------------------------------------------------------
# Deadline buffer
# ---------------------------------------------------------------------------


class TestDeadlineBuffer:
    def test_positive_buffer(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Early arrival → positive buffer."""
        match = _make_feasible_match(available_from=date(2026, 8, 1))

        result = engine.evaluate(match, sample_route, sample_cargo)

        assert result.deadline_buffer_days > 0

    def test_negative_buffer(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Late arrival → negative buffer."""
        # Depart Oct 10, speed 12 kn, distance 4320 nm → 15 days → Oct 25
        route = Route(
            route_id="R-LATE",
            origin_port_id="CNSHA",
            destination_port_id="INPRT",
            distance_nm=4320.0,
        )
        match = _make_feasible_match(
            available_from=date(2026, 10, 10),
            speed_knots=12.0,
        )

        result = engine.evaluate(match, route, sample_cargo)

        assert result.deadline_buffer_days < 0

    def test_near_zero_buffer(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Arrival very close to deadline → buffer near zero."""
        # Arrive Oct 15 23:00 → ~1 hour before 23:59:59 → buffer ≈ 0.04 days
        route = Route(
            route_id="R-TIGHT",
            origin_port_id="CNSHA",
            destination_port_id="INPRT",
            distance_nm=4308.0,  # 4308/12 = 359 hours = Oct 15 23:00
        )
        match = _make_feasible_match(
            available_from=date(2026, 10, 1),
            speed_knots=12.0,
        )

        result = engine.evaluate(match, route, sample_cargo)

        # Buffer should be very small but positive (~0.04 days ≈ ~1 hour)
        assert 0 < result.deadline_buffer_days < 0.1

    def test_fractional_buffer_preserved(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Buffer should not be truncated to integer days."""
        match = _make_feasible_match(
            available_from=date(2026, 8, 1),
            speed_knots=14.5,
        )

        result = engine.evaluate(match, sample_route, sample_cargo)

        # Buffer should have a fractional component
        fractional = result.deadline_buffer_days - int(result.deadline_buffer_days)
        assert fractional != 0.0, "Buffer should have sub-day precision"


# ---------------------------------------------------------------------------
# Phase 1 + Phase 2 combined feasibility
# ---------------------------------------------------------------------------


class TestCombinedFeasibility:
    def test_phase1_valid_and_deadline_valid(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Phase 1 pass + deadline pass → overall feasible."""
        match = _make_feasible_match(available_from=date(2026, 8, 1))

        result = engine.evaluate(match, sample_route, sample_cargo)

        assert result.phase1_feasible is True
        assert result.deadline_feasible is True
        assert result.feasible is True
        assert result.reasons == []

    def test_phase1_rejected_and_eta_valid(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Phase 1 fail + good ETA → overall INFEASIBLE.

        A Phase 1 rejection cannot be overridden by a good ETA.
        """
        match = _make_rejected_match(
            ["Cargo capacity 50,000 MT is 25,000 MT below the requested 75,000 MT."],
            available_from=date(2026, 8, 1),
        )

        result = engine.evaluate(match, sample_route, sample_cargo)

        assert result.phase1_feasible is False
        assert result.deadline_feasible is True  # ETA is fine
        assert result.feasible is False  # but overall is still infeasible
        assert len(result.reasons) >= 1
        assert "capacity" in result.reasons[0].lower() or "50,000" in result.reasons[0]

    def test_phase1_valid_and_deadline_missed(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Phase 1 pass + deadline miss → overall INFEASIBLE."""
        # Late departure → misses deadline
        route = Route(
            route_id="R-LATE",
            origin_port_id="CNSHA",
            destination_port_id="INPRT",
            distance_nm=4320.0,
        )
        match = _make_feasible_match(
            available_from=date(2026, 10, 10),
            speed_knots=12.0,
        )

        result = engine.evaluate(match, route, sample_cargo)

        assert result.phase1_feasible is True
        assert result.deadline_feasible is False
        assert result.feasible is False

    def test_phase1_rejection_reasons_preserved(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Phase 1 rejection reasons must carry through to the voyage result."""
        original_reasons = [
            "Cargo capacity 50,000 MT is 25,000 MT below the requested 75,000 MT.",
            "Vessel draft 16.5 m exceeds Paradip max draft 14.5 m.",
        ]
        match = _make_rejected_match(
            original_reasons,
            available_from=date(2026, 8, 1),
        )

        result = engine.evaluate(match, sample_route, sample_cargo)

        for reason in original_reasons:
            assert reason in result.reasons


# ---------------------------------------------------------------------------
# Route validation
# ---------------------------------------------------------------------------


class TestRouteValidation:
    def test_route_origin_mismatch_rejected(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Route origin must match cargo origin."""
        wrong_route = Route(
            route_id="R-WRONG",
            origin_port_id="SGSIN",
            destination_port_id="INPRT",
            distance_nm=1850.0,
        )
        match = _make_feasible_match()

        with pytest.raises(ValueError, match="origin"):
            engine.evaluate(match, wrong_route, sample_cargo)

    def test_route_destination_mismatch_rejected(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Route destination must match cargo destination."""
        wrong_route = Route(
            route_id="R-WRONG",
            origin_port_id="CNSHA",
            destination_port_id="INVTZ",
            distance_nm=3520.0,
        )
        match = _make_feasible_match()

        with pytest.raises(ValueError, match="destination"):
            engine.evaluate(match, wrong_route, sample_cargo)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_invalid_route_distance_rejected(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Route with zero/negative distance should fail validation."""
        with pytest.raises(Exception):
            Route(
                route_id="R-BAD",
                origin_port_id="CNSHA",
                destination_port_id="INPRT",
                distance_nm=-100.0,
            )

    def test_invalid_vessel_speed_rejected(
        self,
        engine: VoyageFeasibilityEngine,
        sample_cargo: Cargo,
    ) -> None:
        """Vessel with zero/negative speed should fail validation."""
        with pytest.raises(Exception):
            _make_vessel(speed_knots=-5.0)


# ---------------------------------------------------------------------------
# Assumptions and metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_assumptions_populated(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Every result should include documented assumptions."""
        match = _make_feasible_match()

        result = engine.evaluate(match, sample_route, sample_cargo)

        assert len(result.assumptions) > 0
        # Should mention key limitations
        assumptions_text = " ".join(result.assumptions).lower()
        assert "mock" in assumptions_text or "static" in assumptions_text
        assert "weather" in assumptions_text
        assert "ais" in assumptions_text or "position" in assumptions_text

    def test_evaluated_at_populated(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """Every result should have an evaluated_at timestamp."""
        match = _make_feasible_match()

        result = engine.evaluate(match, sample_route, sample_cargo)

        assert result.evaluated_at is not None


# ---------------------------------------------------------------------------
# evaluate_all
# ---------------------------------------------------------------------------


class TestEvaluateAll:
    def test_evaluate_all_processes_multiple_vessels(
        self,
        engine: VoyageFeasibilityEngine,
        sample_route: Route,
        sample_cargo: Cargo,
    ) -> None:
        """evaluate_all should process every match result."""
        matches = [
            _make_feasible_match(
                vessel_id="V-A",
                vessel_name="MV Alpha",
                available_from=date(2026, 8, 1),
            ),
            _make_feasible_match(
                vessel_id="V-B",
                vessel_name="MV Beta",
                available_from=date(2026, 9, 1),
            ),
        ]

        results = engine.evaluate_all(matches, sample_route, sample_cargo)

        assert len(results) == 2
        result_by_id = {r.vessel.vessel_id: r for r in results}
        assert "V-A" in result_by_id
        assert "V-B" in result_by_id


# ---------------------------------------------------------------------------
# Fixture-based: MV Deadline Runner (Phase 1 pass, Phase 2 fail)
# ---------------------------------------------------------------------------


class TestDeadlineRunnerFixture:
    """MV Deadline Runner (V021) passes ALL Phase 1 constraints but
    arrives after the cargo deadline.  This is verified using the
    actual mock fixtures through the real matching + voyage pipeline."""

    def test_deadline_runner_phase1_passes(self) -> None:
        """V021 should pass all 7 Phase 1 hard constraints."""
        from optimization_engine.data.mock.fixtures import MOCK_VESSELS, PARADIP, SAMPLE_CARGO, SHANGHAI
        from optimization_engine.matching.engine import MatchingEngine

        runner = next(v for v in MOCK_VESSELS if v.vessel_id == "V021")
        engine = MatchingEngine()
        results = engine.match_vessels(SAMPLE_CARGO, [runner], SHANGHAI, PARADIP)

        assert len(results) == 1
        assert results[0].feasible is True
        assert results[0].rejection_reasons == []

    def test_deadline_runner_misses_deadline(self) -> None:
        """V021 should fail Phase 2 deadline feasibility."""
        from optimization_engine.data.mock.fixtures import (
            MOCK_VESSELS, PARADIP, ROUTE_LOOKUP, SAMPLE_CARGO, SHANGHAI,
        )
        from optimization_engine.matching.engine import MatchingEngine

        runner = next(v for v in MOCK_VESSELS if v.vessel_id == "V021")
        matching_engine = MatchingEngine()
        match_results = matching_engine.match_vessels(
            SAMPLE_CARGO, [runner], SHANGHAI, PARADIP
        )

        route = ROUTE_LOOKUP["CNSHA-INPRT"]
        voyage_engine = VoyageFeasibilityEngine()
        voyage_results = voyage_engine.evaluate_all(
            match_results, route, SAMPLE_CARGO
        )

        assert len(voyage_results) == 1
        vr = voyage_results[0]
        assert vr.phase1_feasible is True
        assert vr.deadline_feasible is False
        assert vr.feasible is False
        assert any("deadline" in r.lower() for r in vr.reasons)
        assert vr.deadline_buffer_days < 0

