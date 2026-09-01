"""
Mock data fixtures for development and testing.

All data is **purely fictional** and does not represent real vessels,
ports, or cargo requirements.  IMO/MMSI numbers are fabricated.

These fixtures are injected into the matching engine — the engine
itself never reads from this module directly.  When the backend team's
APIs are ready, a ``BackendVesselRepository`` will replace this data
source while the matching logic remains unchanged.
"""

from __future__ import annotations

from datetime import date

from optimization_engine.decision.models import FreightForecastInput
from optimization_engine.domain.models import Cargo, Port, Route, Vessel, VesselStatus
from optimization_engine.economics.models import VoyageCostInput
from optimization_engine.ranking.models import RankingWeights
from optimization_engine.risk.models import RiskFactorInput, RiskWeights


# ---------------------------------------------------------------------------
# Ports
# ---------------------------------------------------------------------------

SHANGHAI = Port(
    port_id="CNSHA",
    port_name="Shanghai",
    country="China",
    max_draft_m=16.0,
    max_loa_m=350.0,
    max_beam_m=55.0,
)

PARADIP = Port(
    port_id="INPRT",
    port_name="Paradip",
    country="India",
    max_draft_m=14.5,
    max_loa_m=300.0,
    max_beam_m=50.0,
)

VISAKHAPATNAM = Port(
    port_id="INVTZ",
    port_name="Visakhapatnam",
    country="India",
    max_draft_m=17.0,
    max_loa_m=330.0,
    max_beam_m=52.0,
)

ALL_PORTS: list[Port] = [SHANGHAI, PARADIP, VISAKHAPATNAM]

PORT_LOOKUP: dict[str, Port] = {p.port_id: p for p in ALL_PORTS}


# ---------------------------------------------------------------------------
# Sample Cargo
# ---------------------------------------------------------------------------

SAMPLE_CARGO = Cargo(
    cargo_id="CRG-2026-001",
    cargo_type="iron_ore",
    quantity_mt=75_000.0,
    origin_port="CNSHA",
    destination_port="INPRT",
    required_arrival_date=date(2026, 10, 15),
    hazardous=False,
    special_requirements=[],
)


# ---------------------------------------------------------------------------
# Vessels (20 fictional vessels)
# ---------------------------------------------------------------------------

MOCK_VESSELS: list[Vessel] = [
    # ── 1. MV Iron Monarch ── ✅ Valid bulk carrier for iron ore
    Vessel(
        vessel_id="V001",
        vessel_name="MV Iron Monarch",
        imo="IMO0000001",
        mmsi="MMSI000001",
        vessel_type="bulk_carrier",
        dwt_mt=95_000.0,
        cargo_capacity_mt=85_000.0,
        loa_m=250.0,
        beam_m=43.0,
        draft_m=14.0,
        speed_knots=14.5,
        current_location="Singapore Anchorage",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 1),
        cargo_types_supported=["iron_ore", "coal", "grain"],
    ),
    # ── 2. MV Cape Horizon ── ✅ Valid, large Capesize
    Vessel(
        vessel_id="V002",
        vessel_name="MV Cape Horizon",
        imo="IMO0000002",
        mmsi="MMSI000002",
        vessel_type="bulk_carrier",
        dwt_mt=180_000.0,
        cargo_capacity_mt=170_000.0,
        loa_m=290.0,
        beam_m=45.0,
        draft_m=14.5,
        speed_knots=14.0,
        current_location="Port Hedland",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 7, 15),
        cargo_types_supported=["iron_ore", "coal"],
    ),
    # ── 3. MV Coastal Star ── ✅ Valid, exactly meets capacity
    Vessel(
        vessel_id="V003",
        vessel_name="MV Coastal Star",
        imo="IMO0000003",
        mmsi="MMSI000003",
        vessel_type="bulk_carrier",
        dwt_mt=82_000.0,
        cargo_capacity_mt=75_000.0,
        loa_m=230.0,
        beam_m=40.0,
        draft_m=13.5,
        speed_knots=13.0,
        current_location="Busan",
        status=VesselStatus.EN_ROUTE,
        available_from=date(2026, 9, 1),
        cargo_types_supported=["iron_ore", "coal", "bauxite"],
    ),
    # ── 4. MV Ocean Breeze ── ❌ Insufficient capacity (50,000 MT)
    Vessel(
        vessel_id="V004",
        vessel_name="MV Ocean Breeze",
        imo="IMO0000004",
        mmsi="MMSI000004",
        vessel_type="bulk_carrier",
        dwt_mt=58_000.0,
        cargo_capacity_mt=50_000.0,
        loa_m=200.0,
        beam_m=32.0,
        draft_m=12.0,
        speed_knots=13.5,
        current_location="Hong Kong",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 10),
        cargo_types_supported=["iron_ore", "coal"],
    ),
    # ── 5. MV Petro Voyager ── ❌ Tanker — wrong cargo type
    Vessel(
        vessel_id="V005",
        vessel_name="MV Petro Voyager",
        imo="IMO0000005",
        mmsi="MMSI000005",
        vessel_type="tanker",
        dwt_mt=120_000.0,
        cargo_capacity_mt=110_000.0,
        loa_m=260.0,
        beam_m=44.0,
        draft_m=14.0,
        speed_knots=15.0,
        current_location="Fujairah",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 5),
        cargo_types_supported=["crude_oil", "fuel_oil"],
    ),
    # ── 6. MV Deep Draft ── ❌ Excessive draft (16.5 m vs 14.5 m limit)
    Vessel(
        vessel_id="V006",
        vessel_name="MV Deep Draft",
        imo="IMO0000006",
        mmsi="MMSI000006",
        vessel_type="bulk_carrier",
        dwt_mt=200_000.0,
        cargo_capacity_mt=185_000.0,
        loa_m=295.0,
        beam_m=48.0,
        draft_m=16.5,
        speed_knots=14.0,
        current_location="Dampier",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 7, 20),
        cargo_types_supported=["iron_ore", "coal"],
    ),
    # ── 7. MV Long Runner ── ❌ Excessive LOA (310 m vs 300 m limit)
    Vessel(
        vessel_id="V007",
        vessel_name="MV Long Runner",
        imo="IMO0000007",
        mmsi="MMSI000007",
        vessel_type="bulk_carrier",
        dwt_mt=190_000.0,
        cargo_capacity_mt=175_000.0,
        loa_m=310.0,
        beam_m=48.0,
        draft_m=14.0,
        speed_knots=14.5,
        current_location="Richards Bay",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 1),
        cargo_types_supported=["iron_ore", "coal"],
    ),
    # ── 8. MV Wide Beam ── ❌ Excessive beam (52 m vs 50 m limit)
    Vessel(
        vessel_id="V008",
        vessel_name="MV Wide Beam",
        imo="IMO0000008",
        mmsi="MMSI000008",
        vessel_type="bulk_carrier",
        dwt_mt=200_000.0,
        cargo_capacity_mt=180_000.0,
        loa_m=295.0,
        beam_m=52.0,
        draft_m=14.0,
        speed_knots=13.5,
        current_location="Tubarao",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 1),
        cargo_types_supported=["iron_ore"],
    ),
    # ── 9. MV Maintenance Queen ── ❌ Under maintenance
    Vessel(
        vessel_id="V009",
        vessel_name="MV Maintenance Queen",
        imo="IMO0000009",
        mmsi="MMSI000009",
        vessel_type="bulk_carrier",
        dwt_mt=100_000.0,
        cargo_capacity_mt=90_000.0,
        loa_m=250.0,
        beam_m=43.0,
        draft_m=14.0,
        speed_knots=14.0,
        current_location="Kobe Drydock",
        status=VesselStatus.UNDER_MAINTENANCE,
        available_from=date(2026, 8, 1),
        cargo_types_supported=["iron_ore", "coal"],
    ),
    # ── 10. MV Laid Up Lady ── ❌ Laid up / inactive
    Vessel(
        vessel_id="V010",
        vessel_name="MV Laid Up Lady",
        imo="IMO0000010",
        mmsi="MMSI000010",
        vessel_type="bulk_carrier",
        dwt_mt=95_000.0,
        cargo_capacity_mt=85_000.0,
        loa_m=240.0,
        beam_m=42.0,
        draft_m=13.5,
        speed_knots=13.0,
        current_location="Alang Anchorage",
        status=VesselStatus.LAID_UP,
        available_from=date(2026, 8, 1),
        cargo_types_supported=["iron_ore", "coal", "grain"],
    ),
    # ── 11. MV Late Arrival ── ❌ Available too late (after deadline)
    Vessel(
        vessel_id="V011",
        vessel_name="MV Late Arrival",
        imo="IMO0000011",
        mmsi="MMSI000011",
        vessel_type="bulk_carrier",
        dwt_mt=100_000.0,
        cargo_capacity_mt=90_000.0,
        loa_m=255.0,
        beam_m=43.0,
        draft_m=14.0,
        speed_knots=14.5,
        current_location="Rotterdam",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 11, 1),
        cargo_types_supported=["iron_ore", "coal"],
    ),
    # ── 12. MV Tiny Trader ── ❌ Very small (10,000 MT)
    Vessel(
        vessel_id="V012",
        vessel_name="MV Tiny Trader",
        imo="IMO0000012",
        mmsi="MMSI000012",
        vessel_type="general_cargo",
        dwt_mt=12_000.0,
        cargo_capacity_mt=10_000.0,
        loa_m=130.0,
        beam_m=20.0,
        draft_m=8.0,
        speed_knots=12.0,
        current_location="Colombo",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 15),
        cargo_types_supported=["iron_ore", "steel", "general"],
    ),
    # ── 13. MV Gas Carrier ── ❌ LPG carrier — wrong type
    Vessel(
        vessel_id="V013",
        vessel_name="MV Gas Carrier",
        imo="IMO0000013",
        mmsi="MMSI000013",
        vessel_type="lpg_carrier",
        dwt_mt=85_000.0,
        cargo_capacity_mt=78_000.0,
        loa_m=230.0,
        beam_m=36.0,
        draft_m=12.5,
        speed_knots=16.0,
        current_location="Ras Tanura",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 1),
        cargo_types_supported=["lpg", "lng"],
    ),
    # ── 14. MV Draft & Small ── ❌ Multiple failures (draft + capacity)
    Vessel(
        vessel_id="V014",
        vessel_name="MV Draft & Small",
        imo="IMO0000014",
        mmsi="MMSI000014",
        vessel_type="bulk_carrier",
        dwt_mt=55_000.0,
        cargo_capacity_mt=45_000.0,
        loa_m=200.0,
        beam_m=32.0,
        draft_m=15.5,
        speed_knots=13.0,
        current_location="Qingdao",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 10),
        cargo_types_supported=["iron_ore", "coal"],
    ),
    # ── 15. MV Pacific Bulk ── ✅ Valid Panamax
    Vessel(
        vessel_id="V015",
        vessel_name="MV Pacific Bulk",
        imo="IMO0000015",
        mmsi="MMSI000015",
        vessel_type="bulk_carrier",
        dwt_mt=95_000.0,
        cargo_capacity_mt=82_000.0,
        loa_m=245.0,
        beam_m=42.0,
        draft_m=14.0,
        speed_knots=14.5,
        current_location="Kaohsiung",
        status=VesselStatus.LOADING,
        available_from=date(2026, 9, 10),
        cargo_types_supported=["iron_ore", "coal", "grain", "bauxite"],
    ),
    # ── 16. MV Ore Express ── ✅ Valid, dedicated ore carrier
    Vessel(
        vessel_id="V016",
        vessel_name="MV Ore Express",
        imo="IMO0000016",
        mmsi="MMSI000016",
        vessel_type="ore_carrier",
        dwt_mt=160_000.0,
        cargo_capacity_mt=150_000.0,
        loa_m=280.0,
        beam_m=45.0,
        draft_m=14.5,
        speed_knots=14.0,
        current_location="Dalian",
        status=VesselStatus.DISCHARGING,
        available_from=date(2026, 9, 5),
        cargo_types_supported=["iron_ore"],
    ),
    # ── 17. MV Handymax Star ── ❌ Insufficient capacity (45,000 MT)
    Vessel(
        vessel_id="V017",
        vessel_name="MV Handymax Star",
        imo="IMO0000017",
        mmsi="MMSI000017",
        vessel_type="bulk_carrier",
        dwt_mt=52_000.0,
        cargo_capacity_mt=45_000.0,
        loa_m=190.0,
        beam_m=32.0,
        draft_m=12.5,
        speed_knots=14.0,
        current_location="Jakarta",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 20),
        cargo_types_supported=["iron_ore", "coal", "grain"],
    ),
    # ── 18. MV Chemical Dawn ── ❌ Chemical tanker — wrong type
    Vessel(
        vessel_id="V018",
        vessel_name="MV Chemical Dawn",
        imo="IMO0000018",
        mmsi="MMSI000018",
        vessel_type="chemical_tanker",
        dwt_mt=40_000.0,
        cargo_capacity_mt=35_000.0,
        loa_m=180.0,
        beam_m=30.0,
        draft_m=11.0,
        speed_knots=15.0,
        current_location="Mumbai",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 8, 1),
        cargo_types_supported=["chemicals", "vegetable_oil"],
    ),
    # ── 19. MV Mega Mover ── ❌ Excessive LOA (320 m) + beam (54 m)
    Vessel(
        vessel_id="V019",
        vessel_name="MV Mega Mover",
        imo="IMO0000019",
        mmsi="MMSI000019",
        vessel_type="bulk_carrier",
        dwt_mt=250_000.0,
        cargo_capacity_mt=230_000.0,
        loa_m=320.0,
        beam_m=54.0,
        draft_m=14.0,
        speed_knots=14.5,
        current_location="Narvik",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 7, 1),
        cargo_types_supported=["iron_ore", "coal"],
    ),
    # ── 20. MV Eastern Promise ── ✅ Valid, available early
    Vessel(
        vessel_id="V020",
        vessel_name="MV Eastern Promise",
        imo="IMO0000020",
        mmsi="MMSI000020",
        vessel_type="bulk_carrier",
        dwt_mt=88_000.0,
        cargo_capacity_mt=80_000.0,
        loa_m=235.0,
        beam_m=40.0,
        draft_m=13.0,
        speed_knots=14.0,
        current_location="Tianjin",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 7, 25),
        cargo_types_supported=["iron_ore", "coal", "grain"],
    ),
    # ── 21. MV Deadline Runner ── ✅ Phase 1 / ❌ Phase 2 (misses deadline)
    #    Passes ALL Phase 1 hard constraints, but available_from is late
    #    enough that sailing to Paradip at 13 kn takes ~11 days, arriving
    #    ~Oct 19 — well after the Oct 15 deadline.  Demonstrates the
    #    Phase 1 PASS + Phase 2 FAIL scenario.
    Vessel(
        vessel_id="V021",
        vessel_name="MV Deadline Runner",
        imo="IMO0000021",
        mmsi="MMSI000021",
        vessel_type="bulk_carrier",
        dwt_mt=90_000.0,
        cargo_capacity_mt=80_000.0,
        loa_m=240.0,
        beam_m=40.0,
        draft_m=13.5,
        speed_knots=13.0,
        current_location="Shanghai",
        status=VesselStatus.AVAILABLE,
        available_from=date(2026, 10, 8),
        cargo_types_supported=["iron_ore", "coal"],
    ),
]


# ---------------------------------------------------------------------------
# Routes (mock planning distances)
#
# IMPORTANT: These distances are mock planning values used for
# demonstration and development.  They are NOT authoritative
# navigational distances and did not come from AIS or any real
# navigation service.  Real distances will be provided by the
# Geospatial team's routing engine in future phases.
# ---------------------------------------------------------------------------

MOCK_ROUTES: list[Route] = [
    Route(
        route_id="CNSHA-INPRT",
        origin_port_id="CNSHA",
        destination_port_id="INPRT",
        distance_nm=3_450.0,
    ),
    Route(
        route_id="CNSHA-INVTZ",
        origin_port_id="CNSHA",
        destination_port_id="INVTZ",
        distance_nm=3_520.0,
    ),
    Route(
        route_id="SGSIN-INPRT",
        origin_port_id="SGSIN",
        destination_port_id="INPRT",
        distance_nm=1_850.0,
    ),
    Route(
        route_id="LKCMB-INPRT",
        origin_port_id="LKCMB",
        destination_port_id="INPRT",
        distance_nm=950.0,
    ),
    Route(
        route_id="LKCMB-INVTZ",
        origin_port_id="LKCMB",
        destination_port_id="INVTZ",
        distance_nm=680.0,
    ),
    Route(
        route_id="INPRT-CNSHA",
        origin_port_id="INPRT",
        destination_port_id="CNSHA",
        distance_nm=3_450.0,
    ),
]

ROUTE_LOOKUP: dict[str, Route] = {r.route_id: r for r in MOCK_ROUTES}


# ---------------------------------------------------------------------------
# Cost Assumptions (mock demo rates)
#
# IMPORTANT: These rates are mock/demo values for development and
# demonstration.  They do NOT represent live commercial pricing,
# actual freight indices, or real port tariffs.  Real rates will be
# provided by the Backend team's tariff APIs, ML freight forecasts,
# and port authority data in future phases.
# ---------------------------------------------------------------------------

SAMPLE_COST_INPUT = VoyageCostInput(
    # Charter / Freight (freight-per-tonne baseline)
    freight_rate_per_mt=10.00,              # USD/MT

    # Fuel
    fuel_price_per_mt=600.00,               # USD/MT (VLSFO-equivalent)
    fuel_consumption_mt_per_day=35.0,       # MT/day at sea

    # Port charges (destination)
    port_charges_fixed=25_000.00,           # USD per port call
    berth_charge_per_day=2_000.00,          # USD/day
    port_days=3.0,                          # days in port
    pilotage_charge=5_000.00,               # USD
    tug_charge=8_000.00,                    # USD

    # Cargo handling
    cargo_handling_rate_per_mt=4.50,        # USD/MT

    # Waiting / Demurrage
    expected_waiting_days=1.5,              # days waiting for berth
    waiting_cost_per_day=15_000.00,         # USD/day
    expected_demurrage_days=0.0,            # no demurrage in demo
    demurrage_rate_per_day=20_000.00,       # USD/day (rate available)

    # Storage
    storage_days=0.0,                       # no storage in demo
    storage_rate_per_day=500.00,            # USD/day

    # Insurance
    insurance_rate_per_mt=1.20,             # USD/MT

    # Maintenance / Operating
    maintenance_cost_per_day=6_000.00,      # USD/day

    # Tax / Duty (demo default: 0)
    tax_cost=0.0,
    duty_cost=0.0,

    # Other
    other_costs=5_000.00,                   # USD misc

    # Currency
    currency="USD",
)


# ---------------------------------------------------------------------------
# Risk Assumptions (mock demo inputs, Phase 4)
#
# IMPORTANT: These raw factor scores are mock/demo values for
# development and demonstration. They do NOT represent live weather
# data, AIS congestion data, maintenance records, compliance records,
# or incident history. Real values will be provided by the Backend
# (Member 2), Geospatial/AIS (Member 4), and ML (Member 1) teams in
# future phases. predicted_delay_risk_score is intentionally left
# unset here so the engine uses its documented deadline-buffer
# fallback rather than a fabricated ML prediction.
# ---------------------------------------------------------------------------

SAMPLE_RISK_INPUT = RiskFactorInput(
    weather_risk_score=25.0,          # mock: mild-moderate seasonal weather
    congestion_risk_score=30.0,       # mock: moderate port congestion
    vessel_age_years=None,            # unknown -> documented default used
    vessel_condition_score=15.0,      # mock: well-maintained vessel
    route_hazard_score=10.0,          # mock: no known hazard zones on route
    port_restriction_score=15.0,      # mock: minor tidal/draft restrictions
    cargo_hazard_override=None,       # derived from Cargo.hazardous instead
    documentation_compliance_score=10.0,  # mock: documentation in order
    predicted_delay_risk_score=None,  # no ML forecast -> deadline-buffer fallback used
    historical_incident_score=5.0,    # mock: clean incident history
)

# Default configurable weights (sum to 1.0; see RiskWeights for formula).
SAMPLE_RISK_WEIGHTS = RiskWeights()


# ---------------------------------------------------------------------------
# Ranking Weights (mock demo configuration, Phase 5)
#
# Default configurable weights (sum to 1.0; see RankingWeights for
# formula). These prioritize cost, then risk and deadline buffer
# equally, then the three vessel-property components equally.
# ---------------------------------------------------------------------------

SAMPLE_RANKING_WEIGHTS = RankingWeights()


# ---------------------------------------------------------------------------
# Freight Forecast (mock demo input, Phase 6)
#
# IMPORTANT: This is a MOCK forecast for development/demo purposes.
# It does NOT represent a live ML prediction. The typed
# ``FreightForecastInput`` contract is the same shape Member 1's real
# freight-forecasting model will eventually populate — only the
# ``source`` label changes from "mock" to something like "member1_ml".
# ---------------------------------------------------------------------------

MOCK_FREIGHT_FORECAST = FreightForecastInput(
    current_freight_rate_per_mt=6.67,
    predicted_freight_rate_per_mt=6.10,
    forecast_horizon_days=5.0,
    confidence=0.72,
    lower_bound_per_mt=5.80,
    upper_bound_per_mt=6.40,
    source="mock",
)
