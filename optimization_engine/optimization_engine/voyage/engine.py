"""
Voyage Feasibility Engine (Phase 2).

Determines whether a vessel that passed Phase 1 static compatibility
can actually reach the destination within the required arrival deadline.

Architecture:
    - **Separate from MatchingEngine** — this engine receives Phase 1
      results as input and adds voyage-timing analysis.
    - **Route-agnostic** — receives ``distance_nm`` via a ``Route`` object;
      does not discover or calculate routes.
    - **Data-source agnostic** — consumes typed domain models; no DB/API.

Baseline ETA model:
    estimated_departure = vessel.available_from (at 00:00)
    sailing_hours       = distance_nm / speed_knots
    estimated_arrival   = estimated_departure + sailing_duration

Critical assumptions (Phase 2 baseline):
    - Vessel is assumed ready at the origin port on ``available_from``.
    - ``current_location`` is intentionally unused because real
      vessel-position routing belongs to the Geospatial/AIS component.
    - Speed is constant; no weather, currents, or congestion.
    - No port waiting, berth delays, or loading/unloading time.

Deadline interpretation:
    A ``required_arrival_date`` of 15 October 2026 means the vessel
    must arrive by **the end of that calendar day** (23:59:59).  This
    prevents a vessel arriving at noon from being incorrectly classified
    as late.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from optimization_engine.domain.models import (
    Cargo,
    MatchResult,
    Route,
    VoyageFeasibilityResult,
)
from optimization_engine.voyage.sailing import (
    calculate_sailing_days,
    calculate_sailing_hours,
)


# ---------------------------------------------------------------------------
# Baseline assumptions included in every Phase 2 result
# ---------------------------------------------------------------------------

_BASELINE_ASSUMPTIONS: list[str] = [
    "Route distance is a mock/static planning value, not an authoritative navigational distance.",
    "Vessel speed is assumed constant throughout the voyage.",
    "Vessel is assumed ready at the origin port on its available_from date.",
    "Current AIS position is not used for departure estimation.",
    "Weather, ocean currents, and wave conditions are not modeled.",
    "Port waiting time and berth availability are not modeled.",
    "Loading/unloading duration is not modeled.",
    "Port congestion is not modeled.",
    "Navigable route optimization is not modeled.",
]


class VoyageFeasibilityEngine:
    """Evaluates voyage-timing feasibility for vessels against a deadline.

    Usage::

        matching_engine = MatchingEngine()
        voyage_engine = VoyageFeasibilityEngine()

        match_results = matching_engine.match_vessels(cargo, vessels, ...)
        voyage_results = voyage_engine.evaluate_all(match_results, route, cargo)

        for vr in voyage_results:
            if vr.feasible:
                print(vr.vessel.vessel_name, "can make the deadline")
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        match_result: MatchResult,
        route: Route,
        cargo: Cargo,
    ) -> VoyageFeasibilityResult:
        """Evaluate voyage feasibility for a single vessel.

        Args:
            match_result: Phase 1 matching result for this vessel.
            route: Route with distance in nautical miles.  Must match
                the cargo's origin and destination ports.
            cargo: Cargo requirement with the arrival deadline.

        Returns:
            A ``VoyageFeasibilityResult`` with full timing analysis.

        Raises:
            ValueError: If the route does not match the cargo's
                origin/destination, or if distance/speed is invalid.
        """
        # 1. Validate route matches cargo
        self._validate_route(route, cargo)

        vessel = match_result.vessel

        # 2. Calculate sailing duration
        sailing_hours = calculate_sailing_hours(
            route.distance_nm, vessel.speed_knots
        )
        sailing_days = calculate_sailing_days(sailing_hours)

        # 3. Estimated departure (baseline: start of available_from day)
        estimated_departure = datetime.combine(
            vessel.available_from, time.min
        )

        # 4. Estimated arrival
        estimated_arrival = estimated_departure + timedelta(
            hours=sailing_hours
        )

        # 5. Construct deadline (end of required arrival date)
        deadline = datetime.combine(
            cargo.required_arrival_date, time(23, 59, 59)
        )

        # 6. Deadline buffer (preserves fractional-day precision)
        deadline_buffer_days = (
            (deadline - estimated_arrival).total_seconds() / 86400
        )

        # 7. Deadline feasibility
        deadline_feasible = estimated_arrival <= deadline

        # 8. Overall feasibility (Phase 1 AND Phase 2)
        phase1_feasible = match_result.feasible
        feasible = phase1_feasible and deadline_feasible

        # 9. Collect all reasons
        reasons: list[str] = list(match_result.rejection_reasons)
        if not deadline_feasible:
            reasons.append(
                f"Estimated arrival is "
                f"{estimated_arrival.strftime('%d %B %Y at %H:%M')}, "
                f"after the required arrival deadline of "
                f"{cargo.required_arrival_date.strftime('%d %B %Y')}."
            )

        return VoyageFeasibilityResult(
            vessel=vessel,
            route=route,
            estimated_departure=estimated_departure,
            sailing_hours=sailing_hours,
            sailing_days=sailing_days,
            estimated_arrival=estimated_arrival,
            required_arrival=cargo.required_arrival_date,
            deadline_buffer_days=deadline_buffer_days,
            deadline_feasible=deadline_feasible,
            phase1_feasible=phase1_feasible,
            feasible=feasible,
            reasons=reasons,
            assumptions=list(_BASELINE_ASSUMPTIONS),
        )

    def evaluate_all(
        self,
        match_results: list[MatchResult],
        route: Route,
        cargo: Cargo,
    ) -> list[VoyageFeasibilityResult]:
        """Evaluate voyage feasibility for multiple vessels.

        Args:
            match_results: Phase 1 matching results.
            route: Route (same for all vessels in this batch).
            cargo: Cargo requirement.

        Returns:
            A list of ``VoyageFeasibilityResult`` — one per vessel.

        Raises:
            ValueError: If the route does not match the cargo's
                origin/destination.
        """
        return [
            self.evaluate(mr, route, cargo) for mr in match_results
        ]

    # ------------------------------------------------------------------
    # Internal validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_route(route: Route, cargo: Cargo) -> None:
        """Verify that the route corresponds to the cargo request."""
        if route.origin_port_id != cargo.origin_port:
            raise ValueError(
                f"Route origin '{route.origin_port_id}' does not match "
                f"cargo origin '{cargo.origin_port}'."
            )
        if route.destination_port_id != cargo.destination_port:
            raise ValueError(
                f"Route destination '{route.destination_port_id}' does "
                f"not match cargo destination '{cargo.destination_port}'."
            )
