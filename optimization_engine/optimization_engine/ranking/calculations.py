"""
Pure calculation functions for vessel ranking.

Each function is deterministic, side-effect-free, and independently
testable — no ML, no OR-Tools, no solver of any kind. Ranking is a
transparent weighted-sum of six 0-100 "goodness" scores (higher is
always better), where:

    - cost, risk            : scored *relative to the other feasible
                               candidates in this batch* (cheapest /
                               safest scores 100), since there is no
                               universal "good" cost or risk value —
                               only "better than the alternatives."
    - deadline_buffer        : also scored batch-relative, for the
                               same reason.
    - cargo_suitability,
      availability,
      operational_suitability: scored *absolutely* from the vessel's
                               own properties, since these have a
                               meaningful standalone interpretation
                               (e.g. an AVAILABLE vessel is
                               operationally ready regardless of what
                               other candidates exist).

This mixed design is a documented methodology choice, not a hidden
assumption — see ``RankingEngine`` for how it surfaces in
``assumptions``.
"""

from __future__ import annotations

from datetime import date

from optimization_engine.domain.models import VesselStatus
from optimization_engine.risk.calculations import (
    calculate_weighted_contribution,
    normalize_weights,
)

# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp ``value`` into the inclusive range [lo, hi].

    Used everywhere a computed ranking score must stay within the
    common 0-100 scale, regardless of how extreme the raw inputs are.
    """
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


# NOTE: normalize_weights() and calculate_weighted_contribution() are
# genuinely identical formulas to Phase 4's risk-weighting math (both
# just "scale a dict of weights to sum to 1.0" and "score × weight").
# Rather than maintain two copies, they are imported from
# risk/calculations.py and re-exported here — ranking already depends
# on risk.models elsewhere (RiskCategory), so this doesn't introduce a
# new coupling direction, just reuses it for a trivial shared utility.


def calculate_overall_rank_score(weighted_contributions: list[float]) -> float:
    """Sum weighted contributions into the overall 0-100 ranking score."""
    return clamp(sum(weighted_contributions))


# ---------------------------------------------------------------------------
# Batch-relative scoring (cost, risk, deadline buffer)
# ---------------------------------------------------------------------------


def calculate_batch_relative_score(
    value: float, min_value: float, max_value: float, higher_is_better: bool
) -> float:
    """Score one candidate's raw value relative to the batch's min/max.

    The best value in the batch always scores 100; the worst always
    scores 0. If every candidate has the same value (no signal to
    differentiate on), every candidate scores 100 — a tie is not a
    penalty.

    Args:
        value: This candidate's raw metric value.
        min_value: The minimum value across all candidates in the batch.
        max_value: The maximum value across all candidates in the batch.
        higher_is_better: True if a larger raw value is more favorable
            (e.g. deadline buffer); False if a smaller raw value is
            more favorable (e.g. cost, risk).

    Returns:
        A 0-100 score, higher is always better.
    """
    if max_value == min_value:
        return 100.0
    if higher_is_better:
        return clamp(100.0 * (value - min_value) / (max_value - min_value))
    return clamp(100.0 * (max_value - value) / (max_value - min_value))


# ---------------------------------------------------------------------------
# Cargo suitability (absolute, from capacity utilization)
# ---------------------------------------------------------------------------


def calculate_cargo_utilization_ratio(quantity_mt: float, cargo_capacity_mt: float) -> float:
    """Fraction of the vessel's capacity the cargo actually uses.

    Args:
        quantity_mt: Cargo quantity in metric tonnes.
        cargo_capacity_mt: Vessel cargo capacity in metric tonnes.

    Returns:
        quantity_mt / cargo_capacity_mt (typically in (0, 1] for
        feasible vessels, since capacity >= quantity is a Phase 1
        hard constraint).

    Raises:
        ValueError: If cargo_capacity_mt is not positive.
    """
    if cargo_capacity_mt <= 0:
        raise ValueError(f"cargo_capacity_mt must be > 0, got {cargo_capacity_mt}.")
    return quantity_mt / cargo_capacity_mt


def calculate_cargo_suitability_score(utilization_ratio: float) -> float:
    """Score capacity utilization, 0-100 — fuller utilization scores higher.

    A vessel that uses nearly all of its capacity for this cargo is
    considered more suitable than one carrying the same cargo in a
    much larger hold (which wastes capacity that could serve other
    cargo). This is a deterministic efficiency proxy, not a
    hard constraint.
    """
    return clamp(100.0 * utilization_ratio)


# ---------------------------------------------------------------------------
# Availability (absolute, from scheduling lead time)
# ---------------------------------------------------------------------------

_FULL_SCORE_LEAD_DAYS = 30.0


def calculate_availability_lead_days(required_arrival_date: date, available_from: date) -> float:
    """Days between when the vessel becomes available and the cargo deadline.

    Args:
        required_arrival_date: Cargo deadline.
        available_from: Date the vessel becomes available.

    Returns:
        (required_arrival_date - available_from).days. Larger is more
        scheduling flexibility.
    """
    return (required_arrival_date - available_from).days


def calculate_availability_score(
    lead_days: float, full_score_lead_days: float = _FULL_SCORE_LEAD_DAYS
) -> float:
    """Score scheduling lead time, 0-100 — more lead time scores higher.

    Linear ramp from 0 (vessel becomes available on the deadline
    itself, or later) up to 100 (``full_score_lead_days`` or more of
    lead time). Negative lead time (vessel available after the
    deadline) clamps to 0 — such vessels should already be excluded
    by Phase 1's availability-window hard constraint.

    Args:
        lead_days: Output of ``calculate_availability_lead_days``.
        full_score_lead_days: Lead time, in days, at which the score
            saturates at 100. Configurable.

    Returns:
        A 0-100 score.
    """
    if full_score_lead_days <= 0:
        raise ValueError(f"full_score_lead_days must be > 0, got {full_score_lead_days}.")
    return clamp(100.0 * lead_days / full_score_lead_days)


# ---------------------------------------------------------------------------
# Operational suitability (absolute, from vessel status)
# ---------------------------------------------------------------------------

# Mock/default scores for each operationally-ready status. UNDER_MAINTENANCE
# and LAID_UP are hard-excluded by Phase 1 and should never reach this
# function in practice; they are included defensively with a score of 0.
OPERATIONAL_SUITABILITY_SCORES: dict[VesselStatus, float] = {
    VesselStatus.AVAILABLE: 100.0,
    VesselStatus.EN_ROUTE: 75.0,
    VesselStatus.LOADING: 60.0,
    VesselStatus.DISCHARGING: 60.0,
    VesselStatus.UNDER_MAINTENANCE: 0.0,
    VesselStatus.LAID_UP: 0.0,
}

_DEFAULT_OPERATIONAL_SUITABILITY_SCORE = 50.0


def calculate_operational_suitability_score(status: VesselStatus) -> float:
    """Score vessel operational status, 0-100, via a fixed lookup table.

    Args:
        status: Vessel operational status.

    Returns:
        The configured score for ``status``, or a neutral default of
        50.0 for any status not in the table (defensive fallback,
        should not occur with the current ``VesselStatus`` enum).
    """
    return OPERATIONAL_SUITABILITY_SCORES.get(status, _DEFAULT_OPERATIONAL_SUITABILITY_SCORE)
