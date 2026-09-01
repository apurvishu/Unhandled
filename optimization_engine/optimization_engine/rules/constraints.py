"""
Hard-constraint rules for vessel matching.

Each constraint is a **pure function** that evaluates a single feasibility
criterion.  Every function follows the same signature pattern::

    check_<name>(vessel, cargo, port=None) -> ConstraintCheck

Design principles:
    - Pure functions: no side effects, no I/O, no database access.
    - Every check returns a ``ConstraintCheck`` — never raises exceptions
      for business-logic failures.
    - Failed checks include a **human-readable reason** with contextual
      numbers so stakeholders can understand *why* and *by how much*.
    - Port-level constraints (draft, LOA, beam) are **static dimensional
      compatibility** checks — not navigational safety assessments.
"""

from __future__ import annotations

from optimization_engine.domain.models import (
    Cargo,
    ConstraintCheck,
    Port,
    Vessel,
    VesselStatus,
)


# ── Excluded statuses ───────────────────────────────────────────────────────
# These statuses represent vessels that are NOT operationally ready to sail.
_EXCLUDED_STATUSES: frozenset[VesselStatus] = frozenset(
    {VesselStatus.UNDER_MAINTENANCE, VesselStatus.LAID_UP}
)


# ---------------------------------------------------------------------------
# 1. Capacity Check
# ---------------------------------------------------------------------------


def check_capacity(vessel: Vessel, cargo: Cargo) -> ConstraintCheck:
    """Verify that the vessel's cargo capacity can hold the required quantity.

    Args:
        vessel: Candidate vessel.
        cargo: Cargo requirement.

    Returns:
        ConstraintCheck with ``passed=True`` if capacity is sufficient.
    """
    if vessel.cargo_capacity_mt >= cargo.quantity_mt:
        return ConstraintCheck(name="capacity", passed=True)

    shortfall = cargo.quantity_mt - vessel.cargo_capacity_mt
    return ConstraintCheck(
        name="capacity",
        passed=False,
        reason=(
            f"Cargo capacity {vessel.cargo_capacity_mt:,.0f} MT is "
            f"{shortfall:,.0f} MT below the requested {cargo.quantity_mt:,.0f} MT."
        ),
    )


# ---------------------------------------------------------------------------
# 2. Cargo Compatibility Check
# ---------------------------------------------------------------------------


def check_cargo_compatibility(vessel: Vessel, cargo: Cargo) -> ConstraintCheck:
    """Verify that the vessel supports the required cargo type.

    This is an exact string match — no fuzzy matching or category
    hierarchy.

    Args:
        vessel: Candidate vessel.
        cargo: Cargo requirement.

    Returns:
        ConstraintCheck with ``passed=True`` if the cargo type is supported.
    """
    if cargo.cargo_type in vessel.cargo_types_supported:
        return ConstraintCheck(name="cargo_compatibility", passed=True)

    return ConstraintCheck(
        name="cargo_compatibility",
        passed=False,
        reason=(
            f"Vessel does not support cargo type '{cargo.cargo_type}'. "
            f"Supported: {vessel.cargo_types_supported}."
        ),
    )


# ---------------------------------------------------------------------------
# 3. Availability Window Check
# ---------------------------------------------------------------------------


def check_availability_window(vessel: Vessel, cargo: Cargo) -> ConstraintCheck:
    """Verify that the vessel is temporally available within the planning window.

    This checks ``available_from <= required_arrival_date``.  It does
    **not** guarantee the vessel can physically arrive by the deadline —
    that requires ETA calculation (Phase 2).

    ``available_from`` represents *temporal* availability (when does the
    current charter end?).  It is independent of ``status`` (operational
    readiness).

    Args:
        vessel: Candidate vessel.
        cargo: Cargo requirement.

    Returns:
        ConstraintCheck with ``passed=True`` if the vessel is available
        within the planning window.
    """
    if vessel.available_from <= cargo.required_arrival_date:
        return ConstraintCheck(name="availability_window", passed=True)

    return ConstraintCheck(
        name="availability_window",
        passed=False,
        reason=(
            f"Vessel available from {vessel.available_from.isoformat()}, "
            f"which is after the planning window ending "
            f"{cargo.required_arrival_date.isoformat()}."
        ),
    )


# ---------------------------------------------------------------------------
# 4. Status Check (Operational Readiness)
# ---------------------------------------------------------------------------


def check_status(vessel: Vessel, cargo: Cargo) -> ConstraintCheck:
    """Verify that the vessel is operationally ready to sail.

    This is an *operational readiness* gate — can the vessel physically
    undertake a voyage?  It is independent of *temporal* availability
    (``available_from``).

    Currently excluded statuses: UNDER_MAINTENANCE, LAID_UP.

    Args:
        vessel: Candidate vessel.
        cargo: Cargo requirement (unused, accepted for uniform signature).

    Returns:
        ConstraintCheck with ``passed=True`` if the vessel is
        operationally ready.
    """
    if vessel.status not in _EXCLUDED_STATUSES:
        return ConstraintCheck(name="status", passed=True)

    status_label = vessel.status.value.replace("_", " ")
    return ConstraintCheck(
        name="status",
        passed=False,
        reason=f"Vessel is currently {status_label}.",
    )


# ---------------------------------------------------------------------------
# 5. Static Draft Compatibility (port constraint)
# ---------------------------------------------------------------------------


def check_draft_compatibility(vessel: Vessel, port: Port) -> ConstraintCheck:
    """Verify that the vessel's draft fits within the port's limit.

    This is a *static dimensional compatibility* check — can the vessel
    physically fit in the port's channel/berth?  It is **not** a
    navigational safety assessment (tidal windows, under-keel clearance,
    etc. are deferred to future phases).

    Args:
        vessel: Candidate vessel.
        port: Destination port with physical constraints.

    Returns:
        ConstraintCheck with ``passed=True`` if draft is within limits.
    """
    if vessel.draft_m <= port.max_draft_m:
        return ConstraintCheck(name="draft_compatibility", passed=True)

    return ConstraintCheck(
        name="draft_compatibility",
        passed=False,
        reason=(
            f"Vessel draft {vessel.draft_m:.1f} m exceeds "
            f"{port.port_name} max draft {port.max_draft_m:.1f} m."
        ),
    )


# ---------------------------------------------------------------------------
# 6. Static LOA Compatibility (port constraint)
# ---------------------------------------------------------------------------


def check_loa_compatibility(vessel: Vessel, port: Port) -> ConstraintCheck:
    """Verify that the vessel's LOA fits within the port's limit.

    Args:
        vessel: Candidate vessel.
        port: Destination port with physical constraints.

    Returns:
        ConstraintCheck with ``passed=True`` if LOA is within limits.
    """
    if vessel.loa_m <= port.max_loa_m:
        return ConstraintCheck(name="loa_compatibility", passed=True)

    return ConstraintCheck(
        name="loa_compatibility",
        passed=False,
        reason=(
            f"Vessel LOA {vessel.loa_m:.0f} m exceeds "
            f"{port.port_name} max LOA {port.max_loa_m:.0f} m."
        ),
    )


# ---------------------------------------------------------------------------
# 7. Static Beam Compatibility (port constraint)
# ---------------------------------------------------------------------------


def check_beam_compatibility(vessel: Vessel, port: Port) -> ConstraintCheck:
    """Verify that the vessel's beam fits within the port's limit.

    Args:
        vessel: Candidate vessel.
        port: Destination port with physical constraints.

    Returns:
        ConstraintCheck with ``passed=True`` if beam is within limits.
    """
    if vessel.beam_m <= port.max_beam_m:
        return ConstraintCheck(name="beam_compatibility", passed=True)

    return ConstraintCheck(
        name="beam_compatibility",
        passed=False,
        reason=(
            f"Vessel beam {vessel.beam_m:.0f} m exceeds "
            f"{port.port_name} max beam {port.max_beam_m:.0f} m."
        ),
    )
