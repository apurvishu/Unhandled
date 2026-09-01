"""
Voyage Emissions Engine (Phase 9).

Computes optional CO2 emissions from fuel already consumed for a
voyage (typically Phase 3's ``VoyageCostBreakdown.fuel_consumed_mt``).
Emissions are entirely optional in the pipeline — this module makes
no regulatory-compliance claims (e.g. IMO CII/EEXI) and uses a
clearly labeled, configurable default emission factor.
"""

from __future__ import annotations

from optimization_engine.emissions.calculations import (
    calculate_co2_emissions_kg,
    calculate_co2_per_tonne_km_kg,
    calculate_co2_per_tonne_kg,
)
from optimization_engine.emissions.models import (
    DEFAULT_EMISSION_FACTOR_KG_CO2_PER_KG_FUEL,
    EmissionsInput,
    EmissionsResult,
)

_BASELINE_ASSUMPTIONS: list[str] = [
    f"Default emission factor ({DEFAULT_EMISSION_FACTOR_KG_CO2_PER_KG_FUEL} kg CO2/kg fuel) is a "
    "commonly cited approximate figure for heavy fuel oil, NOT a verified current regulatory value.",
    "This module does not claim IMO CII/EEXI or any other regulatory compliance.",
    "Fuel consumption is taken as given (typically from Phase 3's voyage economics); this module "
    "does not model engine efficiency, speed optimization, or alternative fuels.",
]


class EmissionsEngine:
    """Computes CO2 emissions for a voyage, with every unit explicit."""

    def calculate(self, emissions_input: EmissionsInput) -> EmissionsResult:
        """Compute a complete emissions breakdown.

        Args:
            emissions_input: Fuel consumed, distance, cargo quantity,
                and the emission factor to use.

        Returns:
            An ``EmissionsResult`` with CO2 in kg/MT, per-tonne, and
            per-tonne-km.
        """
        co2_kg = calculate_co2_emissions_kg(
            emissions_input.fuel_consumed_mt, emissions_input.emission_factor_kg_co2_per_kg_fuel
        )
        co2_per_tonne = calculate_co2_per_tonne_kg(co2_kg, emissions_input.cargo_quantity_mt)
        co2_per_tonne_km = calculate_co2_per_tonne_km_kg(
            co2_kg, emissions_input.cargo_quantity_mt, emissions_input.distance_nm
        )

        return EmissionsResult(
            fuel_consumed_mt=emissions_input.fuel_consumed_mt,
            emission_factor_used=emissions_input.emission_factor_kg_co2_per_kg_fuel,
            co2_emissions_kg=co2_kg,
            co2_emissions_mt=co2_kg / 1_000.0,
            co2_per_tonne_kg=co2_per_tonne,
            co2_per_tonne_km_kg=co2_per_tonne_km,
            assumptions=list(_BASELINE_ASSUMPTIONS),
        )
