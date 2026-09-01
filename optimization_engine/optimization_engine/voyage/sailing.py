"""
Pure sailing-time calculation functions.

These functions implement the deterministic baseline:

    sailing_hours = distance_nm / speed_knots
    sailing_days  = sailing_hours / 24

Because 1 knot = 1 nautical mile per hour.

Design principles:
    - Pure functions: no side effects, no I/O, no state.
    - Strict input validation: zero/negative values raise ValueError.
    - Independently testable — no dependency on domain models.
    - The ETA engine calls these functions; they do NOT discover routes.

These functions will remain unchanged when real route distances arrive
from the Geospatial team's routing engine.
"""

from __future__ import annotations


def calculate_sailing_hours(distance_nm: float, speed_knots: float) -> float:
    """Calculate sailing duration in hours.

    Formula::

        sailing_hours = distance_nm / speed_knots

    Args:
        distance_nm: Route distance in nautical miles.  Must be > 0.
        speed_knots: Vessel service speed in knots.  Must be > 0.

    Returns:
        Sailing duration in hours.

    Raises:
        ValueError: If distance_nm or speed_knots is <= 0.
    """
    if distance_nm <= 0:
        raise ValueError(
            f"distance_nm must be > 0, got {distance_nm}."
        )
    if speed_knots <= 0:
        raise ValueError(
            f"speed_knots must be > 0, got {speed_knots}."
        )
    return distance_nm / speed_knots


def calculate_sailing_days(sailing_hours: float) -> float:
    """Convert sailing duration from hours to days.

    Formula::

        sailing_days = sailing_hours / 24

    Args:
        sailing_hours: Sailing duration in hours.

    Returns:
        Sailing duration in days (preserves fractional component).
    """
    return sailing_hours / 24.0
