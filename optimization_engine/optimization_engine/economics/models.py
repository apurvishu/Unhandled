"""
Domain models for voyage economics (Phase 3).

These models define the cost inputs (configurable rates/assumptions)
and the cost output (transparent breakdown of every cost component).

All rates are expressed in a configurable currency (default: USD).
Current values are **mock/demo rates** — not live commercial pricing.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class VoyageCostInput(BaseModel):
    """Configurable cost rates and assumptions for a voyage cost calculation.

    Every field represents a rate or assumption that can be replaced
    by real data when the backend/ML teams provide it.  For the
    Phase 3 prototype, mock values are used.

    The baseline charter model is **freight per tonne**.  The model is
    designed so that daily-charter-rate and voyage-charter models can
    be added later without rewriting the economics engine.
    """

    # ── Charter / Freight ─────────────────────────────────────────────
    freight_rate_per_mt: float = Field(
        ...,
        ge=0,
        description="Charter/freight rate per metric tonne of cargo (e.g. USD/MT)",
    )

    # ── Fuel ──────────────────────────────────────────────────────────
    fuel_price_per_mt: float = Field(
        ...,
        ge=0,
        description="Fuel price per metric tonne (e.g. VLSFO price)",
    )
    fuel_consumption_mt_per_day: float = Field(
        ...,
        ge=0,
        description="Estimated daily fuel consumption at sea (MT/day)",
    )

    # ── Port Charges ──────────────────────────────────────────────────
    port_charges_fixed: float = Field(
        default=0.0,
        ge=0,
        description="Fixed port dues per port call",
    )
    berth_charge_per_day: float = Field(
        default=0.0,
        ge=0,
        description="Daily berth charge while in port",
    )
    port_days: float = Field(
        default=0.0,
        ge=0,
        description="Estimated days in port for loading/unloading",
    )
    pilotage_charge: float = Field(
        default=0.0,
        ge=0,
        description="Pilotage charge per port call",
    )
    tug_charge: float = Field(
        default=0.0,
        ge=0,
        description="Tug assistance charge per port call",
    )

    # ── Cargo Handling ────────────────────────────────────────────────
    cargo_handling_rate_per_mt: float = Field(
        default=0.0,
        ge=0,
        description="Cargo handling cost per metric tonne",
    )

    # ── Waiting / Demurrage ───────────────────────────────────────────
    expected_waiting_days: float = Field(
        default=0.0,
        ge=0,
        description="Estimated waiting days before berth allocation",
    )
    waiting_cost_per_day: float = Field(
        default=0.0,
        ge=0,
        description="Daily cost while waiting for berth",
    )
    expected_demurrage_days: float = Field(
        default=0.0,
        ge=0,
        description="Estimated demurrage days beyond allowed laytime",
    )
    demurrage_rate_per_day: float = Field(
        default=0.0,
        ge=0,
        description="Daily demurrage rate",
    )

    # ── Storage ───────────────────────────────────────────────────────
    storage_days: float = Field(
        default=0.0,
        ge=0,
        description="Estimated storage days",
    )
    storage_rate_per_day: float = Field(
        default=0.0,
        ge=0,
        description="Daily storage cost",
    )

    # ── Insurance ─────────────────────────────────────────────────────
    insurance_rate_per_mt: float = Field(
        default=0.0,
        ge=0,
        description="Insurance cost per metric tonne of cargo",
    )

    # ── Maintenance / Operating ───────────────────────────────────────
    maintenance_cost_per_day: float = Field(
        default=0.0,
        ge=0,
        description="Daily vessel maintenance/operating cost",
    )

    # ── Tax / Duty ────────────────────────────────────────────────────
    tax_cost: float = Field(
        default=0.0,
        ge=0,
        description=(
            "Tax amount (demo default: 0).  Actual tax/exemption rules "
            "will come from the project's legal/rules system."
        ),
    )
    duty_cost: float = Field(
        default=0.0,
        ge=0,
        description=(
            "Customs duty amount (demo default: 0).  Actual duty rules "
            "will come from the project's legal/rules system."
        ),
    )

    # ── Other ─────────────────────────────────────────────────────────
    other_costs: float = Field(
        default=0.0,
        ge=0,
        description="Any additional miscellaneous costs",
    )

    # ── Currency ──────────────────────────────────────────────────────
    currency: str = Field(
        default="USD",
        description="Currency code for all monetary values",
    )


class VoyageCostBreakdown(BaseModel):
    """Transparent cost breakdown for a single vessel's voyage.

    Every cost component is individually visible.  The total is the
    sum of all components — never a black-box number.

    ``cost_per_mt`` enables direct comparison of per-tonne economics
    across different vessel/route combinations.
    """

    # ── Identity ──────────────────────────────────────────────────────
    vessel_name: str = Field(..., description="Vessel name for identification")
    vessel_id: str = Field(..., description="Vessel ID for identification")
    route_id: str = Field(..., description="Route identifier")

    # ── Cost Components ───────────────────────────────────────────────
    charter_cost: float = Field(..., description="Charter/freight cost")
    fuel_consumed_mt: float = Field(..., description="Total fuel consumed (MT)")
    fuel_cost: float = Field(..., description="Total fuel cost")
    port_cost: float = Field(..., description="Fixed port dues")
    berth_cost: float = Field(..., description="Berth charges")
    pilotage_cost: float = Field(..., description="Pilotage charges")
    tug_cost: float = Field(..., description="Tug charges")
    cargo_handling_cost: float = Field(..., description="Cargo handling cost")
    waiting_cost: float = Field(..., description="Waiting/anchorage cost")
    demurrage_cost: float = Field(..., description="Demurrage cost")
    storage_cost: float = Field(..., description="Storage cost")
    insurance_cost: float = Field(..., description="Insurance cost")
    maintenance_cost: float = Field(..., description="Maintenance/operating cost")
    tax_cost: float = Field(..., description="Tax cost")
    duty_cost: float = Field(..., description="Customs duty cost")
    other_cost: float = Field(..., description="Other/miscellaneous costs")

    # ── Totals ────────────────────────────────────────────────────────
    total_cost: float = Field(
        ...,
        description="Total voyage cost (sum of all components)",
    )
    cost_per_mt: float = Field(
        ...,
        description="Total cost divided by cargo quantity in MT",
    )

    # ── Metadata ──────────────────────────────────────────────────────
    currency: str = Field(default="USD", description="Currency code")
    assumptions: list[str] = Field(
        default_factory=list,
        description="Documented simplifications and mock-data disclaimers",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of evaluation",
    )
