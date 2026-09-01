"""
Domain models for the Maritime Optimization Engine.

All models use Pydantic v2 for strong typing, validation, and serialization.
These models are the shared vocabulary between every module in the engine:
matching, routing, costing, ranking, and recommendation (future phases).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class VesselStatus(str, Enum):
    """Operational readiness of a vessel.

    This represents whether a vessel is *physically capable of sailing*.
    It is independent of *temporal availability* (``available_from``),
    which tracks when the vessel's current commitment ends.

    Only UNDER_MAINTENANCE and LAID_UP are treated as hard-exclusion
    statuses by the matching engine.  All other statuses are considered
    operationally ready and *potentially available* for chartering.
    """

    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    LOADING = "loading"
    DISCHARGING = "discharging"
    UNDER_MAINTENANCE = "under_maintenance"
    LAID_UP = "laid_up"


# ---------------------------------------------------------------------------
# Core Domain Models
# ---------------------------------------------------------------------------


class Cargo(BaseModel):
    """A cargo requirement submitted for vessel matching.

    Represents *what* needs to be shipped, *where*, and *by when*.
    """

    cargo_id: str = Field(..., description="Unique cargo requirement identifier")
    cargo_type: str = Field(
        ...,
        description="Cargo commodity code, e.g. 'iron_ore', 'coal', 'crude_oil'",
    )
    quantity_mt: float = Field(..., gt=0, description="Required quantity in metric tonnes")
    origin_port: str = Field(..., description="Origin port identifier")
    destination_port: str = Field(..., description="Destination port identifier")
    required_arrival_date: date = Field(
        ...,
        description="Latest acceptable arrival date at destination",
    )
    hazardous: bool = Field(default=False, description="Whether the cargo is hazardous")
    density_factor: Optional[float] = Field(
        default=None,
        description="Optional stowage density factor (tonnes per cubic metre)",
    )
    special_requirements: list[str] = Field(
        default_factory=list,
        description="Any special handling requirements",
    )


class Vessel(BaseModel):
    """A candidate vessel that could be chartered for a cargo.

    Contains physical specifications, operational status, and
    supported cargo types.
    """

    vessel_id: str = Field(..., description="Unique vessel identifier")
    vessel_name: str = Field(..., description="Human-readable vessel name")
    imo: str = Field(..., description="IMO number")
    mmsi: str = Field(..., description="MMSI number")
    vessel_type: str = Field(
        ...,
        description="Vessel classification, e.g. 'bulk_carrier', 'tanker'",
    )
    dwt_mt: float = Field(..., gt=0, description="Deadweight tonnage (metric tonnes)")
    cargo_capacity_mt: float = Field(
        ...,
        gt=0,
        description="Usable cargo capacity (metric tonnes)",
    )
    loa_m: float = Field(..., gt=0, description="Length overall (metres)")
    beam_m: float = Field(..., gt=0, description="Beam / width (metres)")
    draft_m: float = Field(..., gt=0, description="Maximum draft (metres)")
    speed_knots: float = Field(..., gt=0, description="Service speed (knots)")
    current_location: str = Field(..., description="Current position description")
    status: VesselStatus = Field(
        ...,
        description=(
            "Operational readiness — can the vessel physically sail? "
            "Independent of temporal availability (available_from)."
        ),
    )
    available_from: date = Field(
        ...,
        description=(
            "Temporal availability — when does the current charter/commitment end? "
            "Independent of operational readiness (status)."
        ),
    )
    cargo_types_supported: list[str] = Field(
        ...,
        description="List of cargo commodity codes this vessel can carry",
    )


class Port(BaseModel):
    """A port with physical constraints that limit which vessels can call.

    Port constraints are used by the matching engine to reject vessels
    whose dimensions exceed the port's limits.
    """

    port_id: str = Field(..., description="Unique port identifier")
    port_name: str = Field(..., description="Human-readable port name")
    country: str = Field(..., description="Country")
    max_draft_m: float = Field(..., gt=0, description="Maximum allowable vessel draft (metres)")
    max_loa_m: float = Field(..., gt=0, description="Maximum allowable vessel LOA (metres)")
    max_beam_m: float = Field(..., gt=0, description="Maximum allowable vessel beam (metres)")


# ---------------------------------------------------------------------------
# Matching Result Models
# ---------------------------------------------------------------------------


class ConstraintCheck(BaseModel):
    """Result of evaluating a single hard constraint against a vessel.

    Every constraint check records whether it passed and, if it failed,
    a human-readable reason explaining *why* and *by how much*.
    """

    name: str = Field(..., description="Constraint name, e.g. 'capacity', 'draft'")
    passed: bool = Field(..., description="Whether the vessel passed this constraint")
    reason: Optional[str] = Field(
        default=None,
        description="Human-readable rejection reason (None if passed)",
    )


class MatchResult(BaseModel):
    """Complete matching assessment for a single vessel against a cargo.

    Contains the vessel, overall feasibility verdict, individual
    constraint check results, a flat list of rejection reasons for
    easy consumption, and a timestamp recording when the evaluation
    was performed.
    """

    vessel: Vessel
    feasible: bool = Field(
        ...,
        description="True if the vessel passed ALL hard constraints",
    )
    checks: list[ConstraintCheck] = Field(
        ...,
        description="Result of each individual constraint check",
    )
    rejection_reasons: list[str] = Field(
        default_factory=list,
        description="Human-readable rejection reasons (empty if feasible)",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of when this evaluation was performed",
    )


# ---------------------------------------------------------------------------
# Route Model (Phase 2)
# ---------------------------------------------------------------------------


class Route(BaseModel):
    """A shipping route between two ports with a known distance.

    Route distances are provided externally — from mock data now, and
    from the Geospatial team's routing engine later.  The ETA engine
    consumes ``distance_nm`` as an input; it does **not** discover routes.

    .. note::
        Current distances are **mock planning values** and are not
        authoritative navigational distances.
    """

    route_id: str = Field(..., description="Unique route identifier")
    origin_port_id: str = Field(..., description="Origin port identifier")
    destination_port_id: str = Field(..., description="Destination port identifier")
    distance_nm: float = Field(
        ...,
        gt=0,
        description="Route distance in nautical miles (must be > 0)",
    )


# ---------------------------------------------------------------------------
# Voyage Feasibility Result (Phase 2)
# ---------------------------------------------------------------------------


class VoyageFeasibilityResult(BaseModel):
    """Complete voyage feasibility assessment for one vessel on one route.

    Combines Phase 1 static compatibility (from ``MatchResult``) with
    Phase 2 voyage timing (ETA vs deadline) into a single verdict.

    ``feasible`` is ``True`` only when **both** ``phase1_feasible`` AND
    ``deadline_feasible`` are ``True``.  A Phase 1 rejection cannot be
    overridden by a good ETA.

    Datetime fields use naive datetimes (no timezone).  The baseline
    model does not yet incorporate real timezone or position data.
    """

    vessel: Vessel
    route: Route
    estimated_departure: datetime = Field(
        ...,
        description=(
            "Baseline estimated departure.  Currently approximated as "
            "vessel.available_from at 00:00.  Actual departure depends on "
            "vessel position, loading ops, charter terms, port availability."
        ),
    )
    sailing_hours: float = Field(
        ...,
        description="Sailing duration in hours (distance_nm / speed_knots)",
    )
    sailing_days: float = Field(
        ...,
        description="Sailing duration in days (sailing_hours / 24)",
    )
    estimated_arrival: datetime = Field(
        ...,
        description="Estimated arrival datetime (departure + sailing duration)",
    )
    required_arrival: date = Field(
        ...,
        description="Required arrival date from cargo requirement",
    )
    deadline_buffer_days: float = Field(
        ...,
        description=(
            "Days between estimated arrival and deadline.  "
            "Positive = early, zero = exact, negative = late.  "
            "Calculated via total_seconds() / 86400 for sub-day precision."
        ),
    )
    deadline_feasible: bool = Field(
        ...,
        description="True if estimated arrival is on or before the deadline",
    )
    phase1_feasible: bool = Field(
        ...,
        description="Whether the vessel passed Phase 1 hard constraints",
    )
    feasible: bool = Field(
        ...,
        description=(
            "Overall feasibility: True only when both phase1_feasible "
            "AND deadline_feasible are True"
        ),
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="All reasons for infeasibility (Phase 1 + Phase 2)",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Documented simplifications in this assessment",
    )
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of when this evaluation was performed",
    )

