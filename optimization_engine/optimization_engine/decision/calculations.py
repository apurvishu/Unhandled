"""
Pure calculation functions for the charter decision engine.

Deterministic, side-effect-free, independently testable. No ML lives
here — forecast-shaped inputs are always taken as-is from the caller.
"""

from __future__ import annotations


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp ``value`` into the inclusive range [lo, hi]."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def calculate_expected_waiting_cost(
    waiting_cost_per_day: float, congestion_cost_per_day: float, wait_days: float
) -> float:
    """Total mock cost of waiting for ``wait_days``."""
    return (waiting_cost_per_day + congestion_cost_per_day) * wait_days


def calculate_adjusted_cost(total_cost: float, risk_score: float, risk_cost_per_point: float) -> float:
    """Make risk commensurable with dollar cost for alternative comparison.

    ``adjusted_cost`` is a comparison metric only — ``total_cost``
    remains the real, raw dollar figure and must always be preserved
    and reported alongside it (never replaced by this).
    """
    return total_cost + risk_score * risk_cost_per_point


def calculate_predicted_savings_per_mt(
    current_cost_per_mt: float, predicted_cost_per_mt: float
) -> float:
    """Positive if the predicted rate is cheaper than the current rate."""
    return current_cost_per_mt - predicted_cost_per_mt


def calculate_net_expected_benefit(
    current_total_cost: float, projected_total_cost_if_waiting: float
) -> float:
    """Raw-dollar benefit of waiting: current total cost minus the
    projected total cost (forecast freight + waiting/congestion cost)
    if the charterer waits instead. Positive means waiting is cheaper.
    """
    return current_total_cost - projected_total_cost_if_waiting
