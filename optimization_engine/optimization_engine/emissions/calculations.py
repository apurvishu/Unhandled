"""
Pure calculation functions for voyage emissions.

Deterministic, side-effect-free, independently testable. No ML, no
regulatory-compliance claims — these are transparent unit conversions
applied to an explicit, configurable emission factor.
"""

from __future__ import annotations

_NM_TO_KM = 1.852  # exact conversion factor, 1 nautical mile = 1.852 km


def calculate_co2_emissions_kg(fuel_consumed_mt: float, emission_factor_kg_co2_per_kg_fuel: float) -> float:
    """Total CO2 emitted, kg, from fuel burned.

    Args:
        fuel_consumed_mt: Fuel consumed, MT.
        emission_factor_kg_co2_per_kg_fuel: kg CO2 emitted per kg fuel burned.

    Returns:
        CO2 emissions in kg.
    """
    fuel_consumed_kg = fuel_consumed_mt * 1_000.0
    return fuel_consumed_kg * emission_factor_kg_co2_per_kg_fuel


def calculate_co2_per_tonne_kg(co2_emissions_kg: float, cargo_quantity_mt: float) -> float:
    """CO2 emitted per MT of cargo carried, kg/MT.

    Raises:
        ValueError: If cargo_quantity_mt is not positive.
    """
    if cargo_quantity_mt <= 0:
        raise ValueError(f"cargo_quantity_mt must be > 0, got {cargo_quantity_mt}.")
    return co2_emissions_kg / cargo_quantity_mt


def calculate_co2_per_tonne_km_kg(co2_emissions_kg: float, cargo_quantity_mt: float, distance_nm: float) -> float:
    """CO2 emitted per tonne-km, kg/(MT*km) — a standard freight-transport intensity metric.

    Raises:
        ValueError: If cargo_quantity_mt or distance_nm is not positive.
    """
    if cargo_quantity_mt <= 0:
        raise ValueError(f"cargo_quantity_mt must be > 0, got {cargo_quantity_mt}.")
    if distance_nm <= 0:
        raise ValueError(f"distance_nm must be > 0, got {distance_nm}.")
    distance_km = distance_nm * _NM_TO_KM
    tonne_km = cargo_quantity_mt * distance_km
    return co2_emissions_kg / tonne_km
