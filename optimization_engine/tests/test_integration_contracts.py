"""
Tests for integration contracts (Phase 11).

Tests cover:
    - Every mock adapter satisfies its corresponding Protocol
      (structural typing, verified at runtime via isinstance())
    - Adapters return data consistent with the fixture data they wrap
    - AISProvider honestly returns None (no fabricated live data)
    - Core domain/engine modules do not import HTTP/DB/ML frameworks
      (a static import-scan, not a runtime check)
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from optimization_engine.integration.adapters import (
    MockAISProvider,
    MockCargoProvider,
    MockCongestionForecastProvider,
    MockDelayForecastProvider,
    MockFreightForecastProvider,
    MockPortProvider,
    MockRouteProvider,
    MockTariffProvider,
    MockVesselProvider,
)
from optimization_engine.integration.contracts import (
    AISProvider,
    CargoProvider,
    CongestionForecastProvider,
    DelayForecastProvider,
    FreightForecastProvider,
    PortProvider,
    RouteProvider,
    TariffProvider,
    VesselProvider,
)


class TestProtocolConformance:
    """Every mock adapter must satisfy its Protocol via structural typing."""

    def test_vessel_provider(self) -> None:
        assert isinstance(MockVesselProvider(), VesselProvider)

    def test_port_provider(self) -> None:
        assert isinstance(MockPortProvider(), PortProvider)

    def test_cargo_provider(self) -> None:
        assert isinstance(MockCargoProvider(), CargoProvider)

    def test_tariff_provider(self) -> None:
        assert isinstance(MockTariffProvider(), TariffProvider)

    def test_route_provider(self) -> None:
        assert isinstance(MockRouteProvider(), RouteProvider)

    def test_ais_provider(self) -> None:
        assert isinstance(MockAISProvider(), AISProvider)

    def test_freight_forecast_provider(self) -> None:
        assert isinstance(MockFreightForecastProvider(), FreightForecastProvider)

    def test_congestion_forecast_provider(self) -> None:
        assert isinstance(MockCongestionForecastProvider(), CongestionForecastProvider)

    def test_delay_forecast_provider(self) -> None:
        assert isinstance(MockDelayForecastProvider(), DelayForecastProvider)


class TestMockVesselProvider:
    def test_get_known_vessel(self) -> None:
        provider = MockVesselProvider()
        vessel = provider.get_vessel("V001")
        assert vessel is not None
        assert vessel.vessel_id == "V001"

    def test_get_unknown_vessel_returns_none(self) -> None:
        provider = MockVesselProvider()
        assert provider.get_vessel("NOPE") is None

    def test_list_vessels_filtered_by_cargo_type(self) -> None:
        provider = MockVesselProvider()
        all_vessels = provider.list_vessels()
        iron_ore_vessels = provider.list_vessels(cargo_type="iron_ore")
        assert len(iron_ore_vessels) <= len(all_vessels)
        assert all("iron_ore" in v.cargo_types_supported for v in iron_ore_vessels)


class TestMockPortProvider:
    def test_get_known_port(self) -> None:
        provider = MockPortProvider()
        port = provider.get_port("CNSHA")
        assert port is not None
        assert port.port_id == "CNSHA"

    def test_get_unknown_port_returns_none(self) -> None:
        provider = MockPortProvider()
        assert provider.get_port("ZZZZ") is None


class TestMockRouteProvider:
    def test_get_known_route(self) -> None:
        provider = MockRouteProvider()
        route = provider.get_route("CNSHA", "INPRT")
        assert route.route_id == "CNSHA-INPRT"

    def test_get_unknown_route_raises_clear_error(self) -> None:
        provider = MockRouteProvider()
        with pytest.raises(ValueError, match="No mock route"):
            provider.get_route("ZZZZ", "YYYY")

    def test_get_alternative_routes(self) -> None:
        provider = MockRouteProvider()
        routes = provider.get_alternative_routes("CNSHA", "INPRT")
        assert all(r.origin_port_id == "CNSHA" and r.destination_port_id == "INPRT" for r in routes)


class TestMockAISProvider:
    """AIS mock must be honest about having no live data — never fabricate a position."""

    def test_position_is_none(self) -> None:
        provider = MockAISProvider()
        assert provider.get_current_position("V001") is None

    def test_remaining_distance_is_none(self) -> None:
        provider = MockAISProvider()
        assert provider.get_remaining_distance_nm("V001", "INPRT") is None


class TestMockFreightForecastProvider:
    def test_returns_forecast_with_requested_horizon(self) -> None:
        provider = MockFreightForecastProvider()
        forecast = provider.get_forecast("CNSHA-INPRT", horizon_days=12.0)
        assert forecast.forecast_horizon_days == 12.0

    def test_source_is_labeled_mock(self) -> None:
        provider = MockFreightForecastProvider()
        forecast = provider.get_forecast("CNSHA-INPRT", horizon_days=5.0)
        assert forecast.source == "mock"


class TestMockTariffProvider:
    def test_returns_configured_cost_input(self) -> None:
        from optimization_engine.economics.models import VoyageCostInput

        custom = VoyageCostInput(
            freight_rate_per_mt=99.0, fuel_price_per_mt=100.0, fuel_consumption_mt_per_day=10.0,
            port_charges_fixed=0.0, berth_charge_per_day=0.0, port_days=0.0, pilotage_charge=0.0,
            tug_charge=0.0, cargo_handling_rate_per_mt=0.0, expected_waiting_days=0.0,
            waiting_cost_per_day=0.0, expected_demurrage_days=0.0, demurrage_rate_per_day=0.0,
            storage_days=0.0, storage_rate_per_day=0.0, insurance_rate_per_mt=0.0,
            maintenance_cost_per_day=0.0, tax_cost=0.0, duty_cost=0.0, other_costs=0.0, currency="USD",
        )
        provider = MockTariffProvider(cost_input=custom)
        result = provider.get_cost_input("V001", "CNSHA-INPRT")
        assert result.freight_rate_per_mt == 99.0


class TestNoForbiddenFrameworkImports:
    """Static check: core engine code must not import HTTP/DB/ML frameworks."""

    FORBIDDEN_MODULES = {
        "fastapi", "flask", "django", "psycopg2", "sqlalchemy", "asyncpg",
        "requests", "httpx", "urllib3", "torch", "tensorflow", "sklearn",
    }

    def test_no_forbidden_imports_in_optimization_engine(self) -> None:
        root = pathlib.Path(__file__).resolve().parent.parent / "optimization_engine"
        violations = []
        for path in root.rglob("*.py"):
            if "data/mock" in str(path):
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top_level = alias.name.split(".")[0]
                        if top_level in self.FORBIDDEN_MODULES:
                            violations.append(f"{path}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] in self.FORBIDDEN_MODULES:
                        violations.append(f"{path}: from {node.module} import ...")
        assert violations == [], f"Forbidden framework imports found: {violations}"
