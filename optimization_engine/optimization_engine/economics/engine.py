"""
Voyage Economics Engine (Phase 3).

Calculates a transparent cost breakdown for a proposed voyage,
given a voyage feasibility result and configurable cost assumptions.

Architecture:
    - **Separate from MatchingEngine and VoyageFeasibilityEngine** — this
      engine receives feasibility results as input and adds cost analysis.
    - **Data-source agnostic** — consumes typed models; no DB/API.
    - **Rate-replaceable** — all rates come from VoyageCostInput, which
      can later be populated by backend APIs, ML forecasts, or tariff
      databases instead of mock values.

The engine does NOT rank vessels or recommend choices.
That is a future module's responsibility.
"""

from __future__ import annotations

from optimization_engine.domain.models import Cargo, VoyageFeasibilityResult
from optimization_engine.economics.calculations import (
    calculate_berth_cost,
    calculate_cargo_handling_cost,
    calculate_charter_cost,
    calculate_cost_per_mt,
    calculate_demurrage_cost,
    calculate_fuel_consumption,
    calculate_fuel_cost,
    calculate_insurance_cost,
    calculate_maintenance_cost,
    calculate_storage_cost,
    calculate_waiting_cost,
)
from optimization_engine.economics.models import (
    VoyageCostBreakdown,
    VoyageCostInput,
)


# ---------------------------------------------------------------------------
# Baseline assumptions included in every Phase 3 result
# ---------------------------------------------------------------------------

_COST_ASSUMPTIONS: list[str] = [
    "All rates are mock/demo values and do not represent live commercial pricing.",
    "Charter cost uses a freight-per-tonne model; daily charter and voyage charter models are not yet implemented.",
    "Fuel consumption is a constant daily rate; no speed-consumption curve or engine-performance model.",
    "Port charges, pilotage, and tug are simplified fixed/daily rates.",
    "Waiting time is a deterministic input; congestion prediction is not modeled.",
    "Demurrage is a configurable input; actual laytime calculations are not modeled.",
    "Insurance uses a per-tonne rate; no actual underwriting or cargo-value model.",
    "Maintenance is a constant daily rate; no predictive maintenance model.",
    "Tax and duty default to zero; actual tax/exemption rules will come from the project's legal/rules system.",
]


class VoyageEconomicsEngine:
    """Calculates a transparent voyage cost breakdown.

    Usage::

        economics_engine = VoyageEconomicsEngine()
        cost = economics_engine.calculate(voyage_result, cargo, cost_input)

        print(f"Total: {cost.total_cost:,.2f} {cost.currency}")
        print(f"Per MT: {cost.cost_per_mt:,.2f} {cost.currency}/MT")
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(
        self,
        voyage_result: VoyageFeasibilityResult,
        cargo: Cargo,
        cost_input: VoyageCostInput,
    ) -> VoyageCostBreakdown:
        """Calculate a complete voyage cost breakdown.

        Args:
            voyage_result: Phase 2 voyage feasibility result (provides
                vessel info, sailing days, route info).
            cargo: Cargo requirement (provides quantity for per-tonne
                calculations).
            cost_input: Configurable cost rates and assumptions.

        Returns:
            A ``VoyageCostBreakdown`` with every cost component
            individually visible.

        Raises:
            ValueError: If cargo quantity is <= 0.
        """
        sailing_days = voyage_result.sailing_days

        # Total voyage days = sailing + port + waiting
        total_voyage_days = (
            sailing_days
            + cost_input.port_days
            + cost_input.expected_waiting_days
        )

        # ── Individual cost components ────────────────────────────────
        charter_cost = calculate_charter_cost(
            cost_input.freight_rate_per_mt, cargo.quantity_mt
        )

        fuel_consumed_mt = calculate_fuel_consumption(
            cost_input.fuel_consumption_mt_per_day, sailing_days
        )
        fuel_cost = calculate_fuel_cost(
            fuel_consumed_mt, cost_input.fuel_price_per_mt
        )

        port_cost = cost_input.port_charges_fixed

        berth_cost = calculate_berth_cost(
            cost_input.berth_charge_per_day, cost_input.port_days
        )

        pilotage_cost = cost_input.pilotage_charge
        tug_cost = cost_input.tug_charge

        cargo_handling_cost = calculate_cargo_handling_cost(
            cost_input.cargo_handling_rate_per_mt, cargo.quantity_mt
        )

        waiting_cost = calculate_waiting_cost(
            cost_input.waiting_cost_per_day,
            cost_input.expected_waiting_days,
        )

        demurrage_cost = calculate_demurrage_cost(
            cost_input.demurrage_rate_per_day,
            cost_input.expected_demurrage_days,
        )

        storage_cost = calculate_storage_cost(
            cost_input.storage_rate_per_day,
            cost_input.storage_days,
        )

        insurance_cost = calculate_insurance_cost(
            cost_input.insurance_rate_per_mt, cargo.quantity_mt
        )

        maintenance_cost = calculate_maintenance_cost(
            cost_input.maintenance_cost_per_day, total_voyage_days
        )

        tax_cost = cost_input.tax_cost
        duty_cost = cost_input.duty_cost
        other_cost = cost_input.other_costs

        # ── Total ─────────────────────────────────────────────────────
        total_cost = (
            charter_cost
            + fuel_cost
            + port_cost
            + berth_cost
            + pilotage_cost
            + tug_cost
            + cargo_handling_cost
            + waiting_cost
            + demurrage_cost
            + storage_cost
            + insurance_cost
            + maintenance_cost
            + tax_cost
            + duty_cost
            + other_cost
        )

        cost_per_mt = calculate_cost_per_mt(total_cost, cargo.quantity_mt)

        return VoyageCostBreakdown(
            vessel_name=voyage_result.vessel.vessel_name,
            vessel_id=voyage_result.vessel.vessel_id,
            route_id=voyage_result.route.route_id,
            charter_cost=charter_cost,
            fuel_consumed_mt=fuel_consumed_mt,
            fuel_cost=fuel_cost,
            port_cost=port_cost,
            berth_cost=berth_cost,
            pilotage_cost=pilotage_cost,
            tug_cost=tug_cost,
            cargo_handling_cost=cargo_handling_cost,
            waiting_cost=waiting_cost,
            demurrage_cost=demurrage_cost,
            storage_cost=storage_cost,
            insurance_cost=insurance_cost,
            maintenance_cost=maintenance_cost,
            tax_cost=tax_cost,
            duty_cost=duty_cost,
            other_cost=other_cost,
            total_cost=total_cost,
            cost_per_mt=cost_per_mt,
            currency=cost_input.currency,
            assumptions=list(_COST_ASSUMPTIONS),
        )

    def calculate_all(
        self,
        voyage_results: list[VoyageFeasibilityResult],
        cargo: Cargo,
        cost_input: VoyageCostInput,
    ) -> list[VoyageCostBreakdown]:
        """Calculate cost breakdowns for multiple vessels.

        Args:
            voyage_results: Phase 2 feasibility results.
            cargo: Cargo requirement.
            cost_input: Cost rates (same for all vessels in this batch).

        Returns:
            A list of ``VoyageCostBreakdown`` — one per vessel.
        """
        return [
            self.calculate(vr, cargo, cost_input)
            for vr in voyage_results
        ]
