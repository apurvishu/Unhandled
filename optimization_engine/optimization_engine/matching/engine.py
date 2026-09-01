"""
Vessel Matching Engine.

Orchestrates the evaluation of all hard constraints against a set of
candidate vessels for a given cargo requirement.

The engine is **data-source agnostic** — it receives domain models as
arguments and never directly reads from a database, CSV, API, or AIS
service.  Mock data is injected into it; later a ``BackendVesselRepository``
adapter will supply live data using the same domain models.

Design:
    - Runs **every** constraint for every vessel (no short-circuit) so
      that all rejection reasons are collected in a single pass.
    - Returns a list of ``MatchResult`` objects with full audit trails.
    - Provides convenience methods to split results into feasible vs
      rejected.
"""

from __future__ import annotations

from optimization_engine.domain.models import (
    Cargo,
    MatchResult,
    Port,
    Vessel,
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


class MatchingEngine:
    """Evaluates candidate vessels against hard constraints for a cargo.

    Usage::

        engine = MatchingEngine()
        results = engine.match_vessels(cargo, vessels, origin_port, dest_port)

        for r in engine.feasible(results):
            print(r.vessel.vessel_name, "is feasible")

        for r in engine.rejected(results):
            print(r.vessel.vessel_name, "rejected:", r.rejection_reasons)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match_vessels(
        self,
        cargo: Cargo,
        vessels: list[Vessel],
        origin_port: Port,
        destination_port: Port,
    ) -> list[MatchResult]:
        """Evaluate every candidate vessel against all hard constraints.

        Args:
            cargo: The cargo requirement to match against.
            vessels: List of candidate vessels.
            origin_port: Origin port (reserved for future origin-side
                checks; currently unused by constraints).
            destination_port: Destination port whose physical limits are
                checked against vessel dimensions.

        Returns:
            A list of ``MatchResult`` objects — one per vessel — each
            containing the full constraint audit trail.
        """
        return [
            self._evaluate_vessel(cargo, vessel, destination_port)
            for vessel in vessels
        ]

    # ------------------------------------------------------------------
    # Convenience filters
    # ------------------------------------------------------------------

    @staticmethod
    def feasible(results: list[MatchResult]) -> list[MatchResult]:
        """Return only feasible vessels from a set of results."""
        return [r for r in results if r.feasible]

    @staticmethod
    def rejected(results: list[MatchResult]) -> list[MatchResult]:
        """Return only rejected vessels from a set of results."""
        return [r for r in results if not r.feasible]

    # ------------------------------------------------------------------
    # Internal evaluation
    # ------------------------------------------------------------------

    def _evaluate_vessel(
        self,
        cargo: Cargo,
        vessel: Vessel,
        destination_port: Port,
    ) -> MatchResult:
        """Run all hard constraints against a single vessel.

        Every constraint is evaluated regardless of earlier failures so
        that the result contains a **complete** list of rejection reasons.
        """
        checks = [
            # Vessel-level constraints
            check_capacity(vessel, cargo),
            check_cargo_compatibility(vessel, cargo),
            check_availability_window(vessel, cargo),
            check_status(vessel, cargo),
            # Port-level static dimensional compatibility
            check_draft_compatibility(vessel, destination_port),
            check_loa_compatibility(vessel, destination_port),
            check_beam_compatibility(vessel, destination_port),
        ]

        rejection_reasons = [c.reason for c in checks if not c.passed and c.reason]
        feasible = len(rejection_reasons) == 0

        return MatchResult(
            vessel=vessel,
            feasible=feasible,
            checks=checks,
            rejection_reasons=rejection_reasons,
        )
