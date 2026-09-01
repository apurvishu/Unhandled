"""
Pure calculation functions for voyage risk scoring.

Each function is deterministic, side-effect-free, and independently
testable. None of these functions call, train, or approximate a
machine-learning model — they are explicit, documented formulas that
stand in until richer data (or an ML forecast) is available from
another team's system.

Design rationale (mirrors ``economics/calculations.py``):
    - One function per concern enables independent unit testing.
    - Every formula is auditable ("why is this factor scored X?").
    - Any single formula can be replaced later without touching others.
"""

from __future__ import annotations

from optimization_engine.risk.models import RiskCategory


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp ``value`` into the inclusive range [lo, hi].

    Used everywhere a computed risk score must stay within the common
    0-100 scale, regardless of how extreme the raw inputs are.
    """
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


# ---------------------------------------------------------------------------
# Vessel age risk
# ---------------------------------------------------------------------------

_YOUNG_AGE_YEARS = 5.0
_YOUNG_AGE_SCORE = 10.0
_OLD_AGE_YEARS = 25.0
_OLD_AGE_SCORE = 90.0


def calculate_vessel_age_risk_score(age_years: float) -> float:
    """Derive an age-risk score, 0-100, from vessel age in years.

    Deterministic piecewise-linear model:
        - age <= 5 years  -> score 10 (young, low risk)
        - age >= 25 years -> score 90 (old, high risk)
        - otherwise       -> linear interpolation between the two

    Args:
        age_years: Vessel age in years. Must be >= 0.

    Returns:
        Age-risk score in [10, 90].

    Raises:
        ValueError: If age_years is negative.
    """
    if age_years < 0:
        raise ValueError(f"age_years must be >= 0, got {age_years}.")

    if age_years <= _YOUNG_AGE_YEARS:
        return _YOUNG_AGE_SCORE
    if age_years >= _OLD_AGE_YEARS:
        return _OLD_AGE_SCORE

    fraction = (age_years - _YOUNG_AGE_YEARS) / (_OLD_AGE_YEARS - _YOUNG_AGE_YEARS)
    return _YOUNG_AGE_SCORE + fraction * (_OLD_AGE_SCORE - _YOUNG_AGE_SCORE)


# ---------------------------------------------------------------------------
# Cargo hazard risk
# ---------------------------------------------------------------------------

_HAZARDOUS_CARGO_SCORE = 65.0
_NON_HAZARDOUS_CARGO_SCORE = 10.0


def calculate_cargo_hazard_risk_score(hazardous: bool) -> float:
    """Derive a cargo hazard risk score from ``Cargo.hazardous``.

    This is a simple deterministic default, not a hazard classification
    system. Callers with a real hazard rating should supply
    ``RiskFactorInput.cargo_hazard_override`` instead.

    Args:
        hazardous: Whether the cargo is flagged hazardous.

    Returns:
        65.0 if hazardous, else 10.0.
    """
    return _HAZARDOUS_CARGO_SCORE if hazardous else _NON_HAZARDOUS_CARGO_SCORE


# ---------------------------------------------------------------------------
# Predicted delay risk (fallback only — real forecasts are external)
# ---------------------------------------------------------------------------


def calculate_predicted_delay_risk_fallback(deadline_buffer_days: float) -> float:
    """Derive a deterministic delay-risk proxy from the deadline buffer.

    This is used **only** when no external ML delay forecast is
    supplied. It is a transparent placeholder, not a prediction:

        score = clamp(50 - deadline_buffer_days * 5, 0, 100)

    A vessel arriving exactly on the deadline (buffer = 0) scores 50.
    Each day of buffer reduces risk by 5 points; each day of lateness
    increases it by 5 points.

    Args:
        deadline_buffer_days: Days between estimated arrival and
            deadline (positive = early, negative = late).

    Returns:
        Delay-risk proxy score in [0, 100].
    """
    return clamp(50.0 - (deadline_buffer_days * 5.0))


# ---------------------------------------------------------------------------
# Weighting
# ---------------------------------------------------------------------------


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Normalize a dict of non-negative weights so that they sum to 1.0.

    This guarantees the overall risk score stays within [0, 100]
    regardless of how the caller configures raw weight values.

    Args:
        weights: Mapping of factor name to non-negative raw weight.

    Returns:
        A new mapping with the same keys, values scaled to sum to 1.0.

    Raises:
        ValueError: If the total weight is <= 0.
    """
    total = sum(weights.values())
    if total <= 0:
        raise ValueError(f"Total weight must be > 0, got {total}.")
    return {name: value / total for name, value in weights.items()}


def calculate_weighted_contribution(raw_score: float, normalized_weight: float) -> float:
    """Calculate one factor's contribution to the overall score.

    Formula::

        weighted_contribution = raw_score × normalized_weight
    """
    return raw_score * normalized_weight


def calculate_overall_score(weighted_contributions: list[float]) -> float:
    """Sum weighted contributions into the overall 0-100 risk score.

    The result is clamped defensively — with normalized weights this
    is a no-op, but it guarantees the invariant holds even under
    floating-point rounding at the boundary.
    """
    return clamp(sum(weighted_contributions))


# ---------------------------------------------------------------------------
# Risk category classification
# ---------------------------------------------------------------------------


def classify_risk_category(
    overall_score: float,
    low_max: float = 25.0,
    moderate_max: float = 50.0,
    high_max: float = 75.0,
) -> RiskCategory:
    """Classify an overall risk score into a human-readable category.

    Default thresholds (all configurable):
        - score <  25            -> LOW
        - 25 <= score <  50      -> MODERATE
        - 50 <= score <  75      -> HIGH
        - score >= 75            -> SEVERE

    Args:
        overall_score: Overall risk score, 0-100.
        low_max: Upper bound (exclusive) of the LOW band.
        moderate_max: Upper bound (exclusive) of the MODERATE band.
        high_max: Upper bound (exclusive) of the HIGH band.

    Returns:
        The matching ``RiskCategory``.
    """
    if overall_score < low_max:
        return RiskCategory.LOW
    if overall_score < moderate_max:
        return RiskCategory.MODERATE
    if overall_score < high_max:
        return RiskCategory.HIGH
    return RiskCategory.SEVERE
