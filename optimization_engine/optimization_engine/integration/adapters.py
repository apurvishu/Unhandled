"""
Mock Adapters (Phase 11).

Reference implementations of the Protocols in ``contracts.py``, backed
entirely by ``data/mock/fixtures.py``. These exist so the demo (Phase
15) and tests can exercise the full pipeline through the same
Protocol interfaces a real backend/geospatial/ML integration will use
— they are NOT real integrations, hit no database, no HTTP endpoint,
and no ML framework. Every value returned is clearly mock/demo data,
consistent with the rest of this module's fixtures.

When Member 1/2/4's real systems are ready, their own classes should
satisfy the same Protocols (structural typing — no inheritance from
these mock classes is required or expected). These mock adapters
should NOT be used for anything beyond local demos and tests.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from optimization_engine.data.mock.fixtures import (
    MOCK_FREIGHT_FORECAST,
    MOCK_VESSELS,
    PARADIP,
    ROUTE_LOOKUP,
    SAMPLE_COST_INPUT,
    SHANGHAI,
    VISAKHAPATNAM,
)
from optimization_engine.decision.models import FreightForecastInput
from optimization_engine.domain.models import Cargo, Port, Route, Vessel
from optimization_engine.economics.models import VoyageCostInput


class MockVesselProvider:
    """Reference ``VesselProvider`` backed by the fixture fleet. Demo/test only."""

    def __init__(self, vessels: Optional[list[Vessel]] = None) -> None:
        self._vessels = vessels if vessels is not None else MOCK_VESSELS
        self._by_id = {v.vessel_id: v for v in self._vessels}

    def get_vessel(self, vessel_id: str) -> Optional[Vessel]:
        return self._by_id.get(vessel_id)

    def list_vessels(self, cargo_type: Optional[str] = None) -> list[Vessel]:
        if cargo_type is None:
            return list(self._vessels)
        return [v for v in self._vessels if cargo_type in v.cargo_types_supported]


class MockPortProvider:
    """Reference ``PortProvider`` backed by the fixture ports. Demo/test only."""

    def __init__(self, ports: Optional[list[Port]] = None) -> None:
        self._ports = ports if ports is not None else [SHANGHAI, PARADIP, VISAKHAPATNAM]
        self._by_id = {p.port_id: p for p in self._ports}

    def get_port(self, port_id: str) -> Optional[Port]:
        return self._by_id.get(port_id)


class MockCargoProvider:
    """Reference ``CargoProvider`` backed by an in-memory dict. Demo/test only."""

    def __init__(self, cargoes: Optional[list[Cargo]] = None) -> None:
        self._by_id = {c.cargo_id: c for c in (cargoes or [])}

    def get_cargo(self, cargo_id: str) -> Optional[Cargo]:
        return self._by_id.get(cargo_id)


class MockTariffProvider:
    """Reference ``TariffProvider`` returning one fixed mock rate card. Demo/test only.

    Ignores vessel_id/route_id and always returns the same
    ``SAMPLE_COST_INPUT`` — a real implementation would look up
    vessel- and route-specific rates.
    """

    def __init__(self, cost_input: Optional[VoyageCostInput] = None) -> None:
        self._cost_input = cost_input if cost_input is not None else SAMPLE_COST_INPUT

    def get_cost_input(self, vessel_id: str, route_id: str) -> VoyageCostInput:
        return self._cost_input


class MockRouteProvider:
    """Reference ``RouteProvider`` backed by the fixture route lookup. Demo/test only."""

    def __init__(self, routes: Optional[dict[str, Route]] = None) -> None:
        self._routes = routes if routes is not None else ROUTE_LOOKUP

    def get_route(self, origin_port_id: str, destination_port_id: str) -> Route:
        for route in self._routes.values():
            if route.origin_port_id == origin_port_id and route.destination_port_id == destination_port_id:
                return route
        raise ValueError(
            f"No mock route from '{origin_port_id}' to '{destination_port_id}'. "
            "This is a fixture-data gap, not a real routing failure."
        )

    def get_alternative_routes(self, origin_port_id: str, destination_port_id: str) -> list[Route]:
        return [
            r for r in self._routes.values()
            if r.origin_port_id == origin_port_id and r.destination_port_id == destination_port_id
        ]


class MockAISProvider:
    """Reference ``AISProvider`` — always returns None (no live tracking data). Demo/test only.

    This is intentional: no Phase 1-10 engine reads AIS data yet, so
    the honest mock behavior is "unknown," not a fabricated position.
    """

    def get_current_position(self, vessel_id: str) -> Optional[tuple[float, float]]:
        return None

    def get_remaining_distance_nm(self, vessel_id: str, destination_port_id: str) -> Optional[float]:
        return None


class MockFreightForecastProvider:
    """Reference ``FreightForecastProvider`` returning the fixture mock forecast. Demo/test only."""

    def __init__(self, forecast: Optional[FreightForecastInput] = None) -> None:
        self._forecast = forecast if forecast is not None else MOCK_FREIGHT_FORECAST

    def get_forecast(self, route_id: str, horizon_days: float) -> FreightForecastInput:
        return self._forecast.model_copy(update={"forecast_horizon_days": horizon_days})


class MockCongestionForecastProvider:
    """Reference ``CongestionForecastProvider`` returning a fixed mock score. Demo/test only."""

    def __init__(self, score: float = 20.0) -> None:
        self._score = score

    def get_congestion_score(self, port_id: str, eta: datetime) -> float:
        return self._score


class MockDelayForecastProvider:
    """Reference ``DelayForecastProvider`` returning a fixed mock score. Demo/test only."""

    def __init__(self, score: float = 15.0) -> None:
        self._score = score

    def get_predicted_delay_risk(self, vessel_id: str, route_id: str, deadline: date) -> float:
        return self._score
