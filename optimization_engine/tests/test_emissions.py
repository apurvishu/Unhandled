"""
Tests for the emissions engine (Phase 9).

Tests cover unit correctness, zero/negative edge cases, configurable
emission factors, and that no regulatory-compliance claim is implied.
"""

from __future__ import annotations

import pytest

from optimization_engine.emissions.calculations import (
    calculate_co2_emissions_kg,
    calculate_co2_per_tonne_km_kg,
    calculate_co2_per_tonne_kg,
)
from optimization_engine.emissions.engine import EmissionsEngine
from optimization_engine.emissions.models import DEFAULT_EMISSION_FACTOR_KG_CO2_PER_KG_FUEL, EmissionsInput


@pytest.fixture
def engine() -> EmissionsEngine:
    return EmissionsEngine()


class TestCalculations:
    def test_co2_emissions_kg_basic(self) -> None:
        assert calculate_co2_emissions_kg(1.0, 3.0) == pytest.approx(3_000.0)

    def test_co2_emissions_scales_with_fuel(self) -> None:
        assert calculate_co2_emissions_kg(200.0, 3.114) == pytest.approx(200_000.0 * 3.114)

    def test_co2_per_tonne(self) -> None:
        assert calculate_co2_per_tonne_kg(10_000.0, 1_000.0) == pytest.approx(10.0)

    def test_co2_per_tonne_zero_cargo_raises(self) -> None:
        with pytest.raises(ValueError, match="cargo_quantity_mt must be > 0"):
            calculate_co2_per_tonne_kg(1_000.0, 0.0)

    def test_co2_per_tonne_negative_cargo_raises(self) -> None:
        with pytest.raises(ValueError, match="cargo_quantity_mt must be > 0"):
            calculate_co2_per_tonne_kg(1_000.0, -5.0)

    def test_co2_per_tonne_km(self) -> None:
        # 1000 kg CO2, 100 MT cargo, 1 nm (1.852 km) -> 1000 / (100*1.852)
        result = calculate_co2_per_tonne_km_kg(1_000.0, 100.0, 1.0)
        assert result == pytest.approx(1_000.0 / (100.0 * 1.852))

    def test_co2_per_tonne_km_zero_distance_raises(self) -> None:
        with pytest.raises(ValueError, match="distance_nm must be > 0"):
            calculate_co2_per_tonne_km_kg(1_000.0, 100.0, 0.0)

    def test_co2_per_tonne_km_negative_distance_raises(self) -> None:
        with pytest.raises(ValueError, match="distance_nm must be > 0"):
            calculate_co2_per_tonne_km_kg(1_000.0, 100.0, -1.0)


class TestEmissionsEngine:
    def test_full_calculation(self, engine) -> None:
        result = engine.calculate(
            EmissionsInput(fuel_consumed_mt=300.0, distance_nm=3_450.0, cargo_quantity_mt=75_000.0)
        )
        assert result.co2_emissions_kg == pytest.approx(300_000.0 * DEFAULT_EMISSION_FACTOR_KG_CO2_PER_KG_FUEL)
        assert result.co2_emissions_mt == pytest.approx(result.co2_emissions_kg / 1_000.0)
        assert result.co2_per_tonne_kg == pytest.approx(result.co2_emissions_kg / 75_000.0)
        assert result.emission_factor_used == DEFAULT_EMISSION_FACTOR_KG_CO2_PER_KG_FUEL

    def test_custom_emission_factor(self, engine) -> None:
        result = engine.calculate(
            EmissionsInput(
                fuel_consumed_mt=100.0, distance_nm=1_000.0, cargo_quantity_mt=50_000.0,
                emission_factor_kg_co2_per_kg_fuel=3.5,
            )
        )
        assert result.emission_factor_used == 3.5
        assert result.co2_emissions_kg == pytest.approx(100_000.0 * 3.5)

    def test_zero_fuel_gives_zero_emissions(self, engine) -> None:
        result = engine.calculate(
            EmissionsInput(fuel_consumed_mt=0.0, distance_nm=1_000.0, cargo_quantity_mt=50_000.0)
        )
        assert result.co2_emissions_kg == 0.0
        assert result.co2_per_tonne_kg == 0.0

    def test_assumptions_disclose_non_regulatory_nature(self, engine) -> None:
        result = engine.calculate(
            EmissionsInput(fuel_consumed_mt=100.0, distance_nm=1_000.0, cargo_quantity_mt=50_000.0)
        )
        text = " ".join(result.assumptions).lower()
        assert "not a verified" in text or "not claim" in text

    def test_deterministic(self, engine) -> None:
        inp = EmissionsInput(fuel_consumed_mt=250.0, distance_nm=2_500.0, cargo_quantity_mt=60_000.0)
        r1 = engine.calculate(inp)
        r2 = engine.calculate(inp)
        assert r1.co2_emissions_kg == r2.co2_emissions_kg
        assert r1.co2_per_tonne_km_kg == r2.co2_per_tonne_km_kg

    def test_negative_fuel_rejected_by_model_validation(self) -> None:
        with pytest.raises(ValueError):
            EmissionsInput(fuel_consumed_mt=-10.0, distance_nm=1_000.0, cargo_quantity_mt=50_000.0)

    def test_zero_distance_rejected_by_model_validation(self) -> None:
        with pytest.raises(ValueError):
            EmissionsInput(fuel_consumed_mt=100.0, distance_nm=0.0, cargo_quantity_mt=50_000.0)

    def test_zero_cargo_rejected_by_model_validation(self) -> None:
        with pytest.raises(ValueError):
            EmissionsInput(fuel_consumed_mt=100.0, distance_nm=1_000.0, cargo_quantity_mt=0.0)
