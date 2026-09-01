"""
Domain models for optional emissions calculation (Phase 9).

Emissions are computed from fuel already consumed for a voyage
(Phase 3's ``VoyageCostBreakdown.fuel_consumed_mt``) and a configurable
emission factor. This module does not claim regulatory compliance
(e.g. IMO CII/EEXI) — the emission factor is a clearly labeled
mock/default assumption unless the caller supplies a verified one.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

# Mock/default emission factor: kg CO2 emitted per kg of heavy fuel oil
# burned. This is a commonly cited approximate figure, NOT a verified,
# current regulatory value — always treat it as a configurable default.
DEFAULT_EMISSION_FACTOR_KG_CO2_PER_KG_FUEL = 3.114


class EmissionsInput(BaseModel):
    """Configurable inputs for an emissions calculation."""

    fuel_consumed_mt: float = Field(..., ge=0, description="Fuel consumed for the voyage, MT")
    distance_nm: float = Field(..., gt=0, description="Voyage distance, nautical miles")
    cargo_quantity_mt: float = Field(..., gt=0, description="Cargo quantity, MT")
    emission_factor_kg_co2_per_kg_fuel: float = Field(
        default=DEFAULT_EMISSION_FACTOR_KG_CO2_PER_KG_FUEL,
        gt=0,
        description=(
            "kg CO2 per kg fuel burned. Mock/default assumption unless "
            "supplied — NOT a verified current regulatory factor."
        ),
    )


class EmissionsResult(BaseModel):
    """Complete emissions calculation, with every unit explicit."""

    fuel_consumed_mt: float = Field(..., description="Fuel consumed, MT")
    emission_factor_used: float = Field(..., description="kg CO2 per kg fuel, as used in this calculation")
    co2_emissions_kg: float = Field(..., description="Total CO2 emitted, kg")
    co2_emissions_mt: float = Field(..., description="Total CO2 emitted, MT")
    co2_per_tonne_kg: float = Field(..., description="CO2 emitted per MT of cargo, kg/MT")
    co2_per_tonne_km_kg: float = Field(..., description="CO2 emitted per tonne-km, kg/(MT*km)")

    assumptions: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
