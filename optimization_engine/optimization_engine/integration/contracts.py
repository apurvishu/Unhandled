"""
Integration Contracts (Phase 11).

These are typed interfaces — ``typing.Protocol`` classes — describing
exactly what this optimization engine expects from each other team's
system. NOTHING in this file talks to a database, an HTTP endpoint, or
an ML framework. Core business logic elsewhere in this package never
imports FastAPI, PostgreSQL/PostGIS drivers, or a specific ML/vendor
library — the only coupling point to the outside world is that a
concrete class implementing one of these Protocols can be handed to
this engine's entry points (e.g. ``FinalRecommendationEngine.recommend``)
once each team's real system exists.

Because these are ``Protocol`` classes (structural typing, PEP 544), a
concrete implementation does NOT need to inherit from them — it only
needs matching method signatures. This keeps the actual backend/
geospatial/ML implementations completely free to choose their own
class hierarchies, frameworks, and libraries.

Ownership map:
    Member 2 (Backend & Database):    VesselProvider, PortProvider,
                                       CargoProvider, TariffProvider
    Member 4 (Geospatial & AIS):      RouteProvider, AISProvider
    Member 1 (AI/ML):                 FreightForecastProvider,
                                       CongestionForecastProvider,
                                       DelayForecastProvider
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Protocol, runtime_checkable

from optimization_engine.decision.models import FreightForecastInput
from optimization_engine.domain.models import Cargo, Port, Route, Vessel
from optimization_engine.economics.models import VoyageCostInput


# ---------------------------------------------------------------------------
# Member 2 — Backend & Database
# ---------------------------------------------------------------------------


@runtime_checkable
class VesselProvider(Protocol):
    """Supplies vessel data. Backed by Member 2's fleet database."""

    def get_vessel(self, vessel_id: str) -> Optional[Vessel]:
        """Return one vessel by ID, or None if it doesn't exist."""
        ...

    def list_vessels(self, cargo_type: Optional[str] = None) -> list[Vessel]:
        """Return candidate vessels, optionally filtered by supported cargo type."""
        ...


@runtime_checkable
class PortProvider(Protocol):
    """Supplies port physical-limit data. Backed by Member 2's port database."""

    def get_port(self, port_id: str) -> Optional[Port]:
        """Return one port by ID, or None if it doesn't exist."""
        ...


@runtime_checkable
class CargoProvider(Protocol):
    """Supplies cargo requirement data. Backed by Member 2's booking/order system."""

    def get_cargo(self, cargo_id: str) -> Optional[Cargo]:
        """Return one cargo requirement by ID, or None if it doesn't exist."""
        ...


@runtime_checkable
class TariffProvider(Protocol):
    """Supplies current commercial rates. Backed by Member 2's tariff/contract data.

    Returns a fully-populated ``VoyageCostInput`` — this engine never
    invents freight rates, fuel prices, port charges, etc.
    """

    def get_cost_input(self, vessel_id: str, route_id: str) -> VoyageCostInput:
        """Return the current cost assumptions for one vessel/route pair."""
        ...


# ---------------------------------------------------------------------------
# Member 4 — Geospatial & AIS
# ---------------------------------------------------------------------------


@runtime_checkable
class RouteProvider(Protocol):
    """Supplies route distances. Backed by Member 4's routing engine.

    This optimization engine never computes its own navigational
    route — it only ever consumes ``Route`` objects supplied here.
    """

    def get_route(self, origin_port_id: str, destination_port_id: str) -> Route:
        """Return the route between two ports."""
        ...

    def get_alternative_routes(self, origin_port_id: str, destination_port_id: str) -> list[Route]:
        """Return alternative routes between two ports (e.g. Suez vs. Cape), if any."""
        ...


@runtime_checkable
class AISProvider(Protocol):
    """Supplies live vessel tracking data. Backed by Member 4's AIS feed.

    This engine never fabricates a live vessel position — the
    ``Vessel.current_location`` field exists precisely so a real
    ``AISProvider`` can eventually populate it; no Phase 1-10 engine
    currently reads it.
    """

    def get_current_position(self, vessel_id: str) -> Optional[tuple[float, float]]:
        """Return (latitude, longitude) for a vessel, or None if unknown."""
        ...

    def get_remaining_distance_nm(self, vessel_id: str, destination_port_id: str) -> Optional[float]:
        """Return the vessel's remaining distance to a destination, nautical miles."""
        ...


# ---------------------------------------------------------------------------
# Member 1 — AI/ML
# ---------------------------------------------------------------------------


@runtime_checkable
class FreightForecastProvider(Protocol):
    """Supplies freight-rate forecasts. Backed by Member 1's ML model.

    Returns the same typed ``FreightForecastInput`` contract this
    engine's Phase 6 decision logic already understands (see
    ``decision/models.py``) — today it is populated with mock data
    (``fixtures.MOCK_FREIGHT_FORECAST``); this Protocol is what
    Member 1's real model will satisfy instead, with no change
    required on this engine's side.
    """

    def get_forecast(self, route_id: str, horizon_days: float) -> FreightForecastInput:
        """Return a freight-rate forecast for a route at a given horizon."""
        ...


@runtime_checkable
class CongestionForecastProvider(Protocol):
    """Supplies port/route congestion forecasts. Backed by Member 1's ML model.

    Returns a 0-100 risk-style score matching ``RiskFactorInput.congestion_risk_score``'s
    scale (risk/models.py) — this engine never fabricates this value;
    without a provider, ``RiskFactorInput``'s mock default is used instead.
    """

    def get_congestion_score(self, port_id: str, eta: datetime) -> float:
        """Return a 0-100 congestion risk score for a port at an estimated arrival time."""
        ...


@runtime_checkable
class DelayForecastProvider(Protocol):
    """Supplies predicted-delay forecasts. Backed by Member 1's ML model.

    Returns a 0-100 score matching ``RiskFactorInput.predicted_delay_risk_score``'s
    scale. Without a provider, ``RiskEngine`` falls back to a
    deterministic deadline-buffer proxy (see risk/calculations.py),
    clearly flagged as an estimate rather than a real prediction.
    """

    def get_predicted_delay_risk(self, vessel_id: str, route_id: str, deadline: date) -> float:
        """Return a 0-100 predicted delay risk score."""
        ...
