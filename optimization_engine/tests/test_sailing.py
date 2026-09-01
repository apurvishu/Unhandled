"""
Unit tests for sailing-time calculation functions.

Tests cover valid calculations, input validation, and edge cases.
"""

from __future__ import annotations

import pytest

from optimization_engine.voyage.sailing import (
    calculate_sailing_days,
    calculate_sailing_hours,
)


# ---------------------------------------------------------------------------
# calculate_sailing_hours
# ---------------------------------------------------------------------------


class TestSailingHours:
    def test_sailing_hours_basic(self) -> None:
        """2800 nm / 14 kn = 200 hours."""
        result = calculate_sailing_hours(2800.0, 14.0)
        assert result == pytest.approx(200.0)

    def test_sailing_hours_fractional(self) -> None:
        """3450 nm / 14.5 kn = 237.931... hours."""
        result = calculate_sailing_hours(3450.0, 14.5)
        assert result == pytest.approx(237.9310, rel=1e-3)

    def test_zero_distance_rejected(self) -> None:
        with pytest.raises(ValueError, match="distance_nm must be > 0"):
            calculate_sailing_hours(0.0, 14.0)

    def test_negative_distance_rejected(self) -> None:
        with pytest.raises(ValueError, match="distance_nm must be > 0"):
            calculate_sailing_hours(-100.0, 14.0)

    def test_zero_speed_rejected(self) -> None:
        with pytest.raises(ValueError, match="speed_knots must be > 0"):
            calculate_sailing_hours(2800.0, 0.0)

    def test_negative_speed_rejected(self) -> None:
        with pytest.raises(ValueError, match="speed_knots must be > 0"):
            calculate_sailing_hours(2800.0, -5.0)


# ---------------------------------------------------------------------------
# calculate_sailing_days
# ---------------------------------------------------------------------------


class TestSailingDays:
    def test_sailing_days_basic(self) -> None:
        """200 hours = 8.333... days."""
        result = calculate_sailing_days(200.0)
        assert result == pytest.approx(8.3333, rel=1e-3)

    def test_sailing_days_exact(self) -> None:
        """240 hours = exactly 10.0 days."""
        result = calculate_sailing_days(240.0)
        assert result == pytest.approx(10.0)

    def test_sailing_days_fractional(self) -> None:
        """161.538 hours = 6.73075 days."""
        result = calculate_sailing_days(161.538)
        assert result == pytest.approx(6.73075, rel=1e-4)
