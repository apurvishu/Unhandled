"""
Pure cost-calculation functions for voyage economics.

Each function implements a single, transparent cost formula.
All functions are pure — no side effects, no I/O, no state.

Design rationale:
    Individual functions for each cost component enable:
    - Independent unit testing per formula
    - Transparent auditability ("why does fuel cost X?")
    - Future replacement of any single formula without touching others
    - Clear documentation of each cost driver
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Fuel
# ---------------------------------------------------------------------------


def calculate_fuel_consumption(
    consumption_mt_per_day: float,
    sailing_days: float,
) -> float:
    """Calculate total fuel consumed during the voyage.

    Formula::

        fuel_consumed = consumption_mt_per_day × sailing_days

    Args:
        consumption_mt_per_day: Daily fuel consumption (MT/day).
        sailing_days: Duration at sea in days.

    Returns:
        Total fuel consumed in metric tonnes.
    """
    return consumption_mt_per_day * sailing_days


def calculate_fuel_cost(
    fuel_consumed_mt: float,
    fuel_price_per_mt: float,
) -> float:
    """Calculate fuel cost.

    Formula::

        fuel_cost = fuel_consumed × fuel_price_per_mt

    Args:
        fuel_consumed_mt: Fuel consumed in metric tonnes.
        fuel_price_per_mt: Fuel price per metric tonne.

    Returns:
        Total fuel cost.
    """
    return fuel_consumed_mt * fuel_price_per_mt


# ---------------------------------------------------------------------------
# Charter / Freight
# ---------------------------------------------------------------------------


def calculate_charter_cost(
    freight_rate_per_mt: float,
    cargo_quantity_mt: float,
) -> float:
    """Calculate charter/freight cost using the freight-per-tonne model.

    Formula::

        charter_cost = freight_rate_per_mt × cargo_quantity_mt

    This is the baseline charter model.  Future models may add:
    - daily charter rate × voyage days
    - lump-sum voyage charter
    - time charter equivalent

    Args:
        freight_rate_per_mt: Freight rate per metric tonne.
        cargo_quantity_mt: Cargo quantity in metric tonnes.

    Returns:
        Charter/freight cost.
    """
    return freight_rate_per_mt * cargo_quantity_mt


# ---------------------------------------------------------------------------
# Port costs (itemized)
# ---------------------------------------------------------------------------


def calculate_berth_cost(
    berth_charge_per_day: float,
    port_days: float,
) -> float:
    """Calculate berth charges.

    Formula::

        berth_cost = berth_charge_per_day × port_days
    """
    return berth_charge_per_day * port_days


def calculate_cargo_handling_cost(
    cargo_handling_rate_per_mt: float,
    cargo_quantity_mt: float,
) -> float:
    """Calculate cargo handling cost.

    Formula::

        cargo_handling_cost = rate_per_mt × cargo_quantity_mt
    """
    return cargo_handling_rate_per_mt * cargo_quantity_mt


# ---------------------------------------------------------------------------
# Waiting / Demurrage
# ---------------------------------------------------------------------------


def calculate_waiting_cost(
    waiting_cost_per_day: float,
    waiting_days: float,
) -> float:
    """Calculate waiting/anchorage cost.

    Formula::

        waiting_cost = cost_per_day × waiting_days
    """
    return waiting_cost_per_day * waiting_days


def calculate_demurrage_cost(
    demurrage_rate_per_day: float,
    demurrage_days: float,
) -> float:
    """Calculate demurrage cost.

    Formula::

        demurrage_cost = rate_per_day × demurrage_days

    Demurrage is conceptually separate from generic waiting cost.
    """
    return demurrage_rate_per_day * demurrage_days


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


def calculate_storage_cost(
    storage_rate_per_day: float,
    storage_days: float,
) -> float:
    """Calculate storage cost.

    Formula::

        storage_cost = rate_per_day × storage_days
    """
    return storage_rate_per_day * storage_days


# ---------------------------------------------------------------------------
# Insurance
# ---------------------------------------------------------------------------


def calculate_insurance_cost(
    insurance_rate_per_mt: float,
    cargo_quantity_mt: float,
) -> float:
    """Calculate insurance cost.

    Formula::

        insurance_cost = rate_per_mt × cargo_quantity_mt
    """
    return insurance_rate_per_mt * cargo_quantity_mt


# ---------------------------------------------------------------------------
# Maintenance / Operating
# ---------------------------------------------------------------------------


def calculate_maintenance_cost(
    maintenance_cost_per_day: float,
    total_voyage_days: float,
) -> float:
    """Calculate maintenance/operating cost over the full voyage duration.

    Vessel operating costs accrue for the entire voyage including
    sailing, port time, and waiting time.

    Formula::

        maintenance_cost = cost_per_day × total_voyage_days
    """
    return maintenance_cost_per_day * total_voyage_days


# ---------------------------------------------------------------------------
# Cost per tonne
# ---------------------------------------------------------------------------


def calculate_cost_per_mt(
    total_cost: float,
    cargo_quantity_mt: float,
) -> float:
    """Calculate cost per metric tonne.

    Formula::

        cost_per_mt = total_cost / cargo_quantity_mt

    Args:
        total_cost: Total voyage cost.
        cargo_quantity_mt: Cargo quantity in metric tonnes.  Must be > 0.

    Returns:
        Cost per metric tonne.

    Raises:
        ValueError: If cargo_quantity_mt is <= 0.
    """
    if cargo_quantity_mt <= 0:
        raise ValueError(
            f"cargo_quantity_mt must be > 0, got {cargo_quantity_mt}."
        )
    return total_cost / cargo_quantity_mt
