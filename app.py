from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import st_folium

from services.ais_simulator import advance_ais_positions
from services.risk_engine import (
    add_risk_to_vessels,
    build_port_risk_summary,
)
from services.charter_advisor import build_charter_shortlist
from services.geo_utils import (
    haversine_nm,
    get_eta_hours,
    get_vessel_status,
    check_compatibility,
    get_congestion_level,
    estimate_wait_days,
)


st.set_page_config(
    page_title="Vessel & Port Intelligence",
    layout="wide"
)


def get_marker_colour(status, compatible):
    if not compatible:
        return "red"

    if status == "BERTHED":
        return "green"

    if status == "WAITING AT ANCHORAGE":
        return "orange"

    return "blue"


# ------------------------------------------------
# Load original data
# ------------------------------------------------

project_folder = Path(__file__).resolve().parent
data_folder = project_folder / "data"

try:
    ports = pd.read_csv(data_folder / "ports.csv")
    vessels = pd.read_csv(data_folder / "vessels.csv")
    source_ais = pd.read_csv(data_folder / "ais_positions.csv")

except FileNotFoundError:
    st.error(
        "CSV file not found. Check the data folder and file names."
    )
    st.stop()


ports["port_id"] = ports["port_id"].astype(str)
vessels["mmsi"] = vessels["mmsi"].astype(str)
source_ais["mmsi"] = source_ais["mmsi"].astype(str)
source_ais["timestamp"] = pd.to_datetime(source_ais["timestamp"])

port_lookup = ports.set_index("port_id").to_dict("index")


# ------------------------------------------------
# Simulation state and controls
# ------------------------------------------------

st.session_state.setdefault(
    "simulated_ais",
    source_ais.copy()
)

st.session_state.setdefault(
    "last_auto_tick",
    0
)

st.session_state.setdefault(
    "simulator_running",
    False
)

st.session_state.setdefault(
    "simulation_hours",
    6
)


with st.sidebar:
    st.header("AIS simulator")

    st.caption(
        "Each tick moves every vessel by a selected number of virtual hours."
    )

    auto_simulation = st.toggle(
        "Automatic simulation",
        key="simulator_running"
    )

    virtual_hours = st.slider(
        "Virtual hours per tick",
        min_value=1,
        max_value=24,
        value=6,
        key="simulation_hours"
    )

    advance_clicked = st.button(
        ":material/play_arrow: Advance simulation"
    )

    reset_clicked = st.button(
        ":material/restart_alt: Reset simulation"
    )


# One automatic page refresh every five seconds.
# The limit prevents endless simulation during a demo.
if auto_simulation:
    refresh_count = st_autorefresh(
        interval=5000,
        limit=120,
        key="ais_simulator_clock"
    )
else:
    refresh_count = 0


# Reset back to the CSV data
if reset_clicked:
    st.session_state["simulated_ais"] = source_ais.copy()
    st.session_state["last_auto_tick"] = refresh_count

# Advance one manual simulation tick
elif advance_clicked:
    st.session_state["simulated_ais"] = advance_ais_positions(
        st.session_state["simulated_ais"],
        port_lookup,
        virtual_hours
    )
    st.session_state["last_auto_tick"] = refresh_count

# Advance automatically after every timed refresh
elif (
    auto_simulation
    and refresh_count > st.session_state["last_auto_tick"]
):
    st.session_state["simulated_ais"] = advance_ais_positions(
        st.session_state["simulated_ais"],
        port_lookup,
        virtual_hours
    )
    st.session_state["last_auto_tick"] = refresh_count


# Use simulation data for all map calculations
ais = st.session_state["simulated_ais"].copy()


# ------------------------------------------------
# Select latest AIS position for every vessel
# ------------------------------------------------

latest_ais = (
    ais.sort_values("timestamp")
    .groupby("mmsi", as_index=False)
    .tail(1)
)

latest_vessels = latest_ais.merge(
    vessels,
    on="mmsi",
    how="left"
)


# ------------------------------------------------
# Geospatial calculations
# ------------------------------------------------

enriched_vessels = []

for vessel in latest_vessels.to_dict("records"):
    destination_id = str(vessel["destination"])
    destination_port = port_lookup.get(destination_id)

    if destination_port is None:
        continue

    distance_nm = haversine_nm(
        vessel["latitude"],
        vessel["longitude"],
        destination_port["latitude"],
        destination_port["longitude"]
    )

    status = get_vessel_status(
        distance_nm,
        vessel["speed_knots"],
        destination_port["anchorage_radius_nm"]
    )

    eta = get_eta_hours(
        distance_nm,
        vessel["speed_knots"]
    )

    compatible, compatibility_issue = check_compatibility(
        vessel,
        destination_port
    )

    vessel["destination_name"] = destination_port["name"]
    vessel["distance_remaining_nm"] = distance_nm
    vessel["status"] = status
    vessel["eta_hours"] = eta
    vessel["compatible"] = compatible
    vessel["compatibility_issue"] = compatibility_issue

    enriched_vessels.append(vessel)


latest_vessels = pd.DataFrame(enriched_vessels)

if latest_vessels.empty:
    st.error("No valid vessel records were found.")
    st.stop()


# ------------------------------------------------
# Port congestion calculations
# ------------------------------------------------

waiting_vessels = latest_vessels[
    latest_vessels["status"] == "WAITING AT ANCHORAGE"
]

waiting_count_by_port = (
    waiting_vessels
    .groupby("destination")
    .size()
    .to_dict()
)
latest_vessels = add_risk_to_vessels(
    latest_vessels,
    waiting_count_by_port
)

port_risk_summary = build_port_risk_summary(
    ports,
    waiting_count_by_port
)


# ------------------------------------------------
# Dashboard heading and metrics
# ------------------------------------------------

st.title(":material/directions_boat: Vessel & Port Intelligence")

if auto_simulation:
    st.caption(
        "Simulation is running. The map updates every five seconds."
    )
else:
    st.caption(
        "Simulation is paused. Use the sidebar to advance vessels manually."
    )

total_vessels = len(latest_vessels)
underway_count = len(
    latest_vessels[latest_vessels["status"] == "UNDERWAY"]
)
waiting_count = len(
    latest_vessels[
        latest_vessels["status"] == "WAITING AT ANCHORAGE"
    ]
)
incompatible_count = len(
    latest_vessels[latest_vessels["compatible"] == False]
)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

metric_1.metric("Total vessels", total_vessels)
metric_2.metric("Underway", underway_count)
metric_3.metric("Waiting at anchorage", waiting_count)
metric_4.metric("Port-incompatible vessels", incompatible_count)
# ------------------------------------------------
# Charter planning and vessel recommendation
# ------------------------------------------------

st.divider()
st.subheader(":material/assignment: Charter planning")

st.caption(
    "Prototype assumption: every tracked vessel is available, "
    "and DWT is used as cargo capacity."
)

with st.form("charter_planning_form"):
    input_col_1, input_col_2, input_col_3 = st.columns(3)

    with input_col_1:
        requested_cargo_tonnes = st.number_input(
            "Cargo quantity (tonnes)",
            min_value=1_000,
            max_value=300_000,
            value=50_000,
            step=5_000,
        )

    with input_col_2:
        requested_port_id = st.selectbox(
            "Destination port",
            options=ports["port_id"].tolist(),
            format_func=lambda port_id: (
                f"{port_lookup[port_id]['name']} ({port_id})"
            ),
        )

    with input_col_3:
        requested_delivery_days = st.number_input(
            "Required arrival within (days)",
            min_value=1,
            max_value=60,
            value=14,
            step=1,
        )

    shortlist_clicked = st.form_submit_button(
        ":material/rocket_launch: Generate shortlist"
    )

if shortlist_clicked:
    st.session_state["charter_request"] = {
        "cargo_tonnes": requested_cargo_tonnes,
        "port_id": requested_port_id,
        "delivery_days": requested_delivery_days,
    }

charter_request = st.session_state.get("charter_request")

if charter_request:
    requested_port = port_lookup[charter_request["port_id"]]

    port_waiting_vessels = waiting_count_by_port.get(
        charter_request["port_id"],
        0,
    )

    charter_shortlist = build_charter_shortlist(
        candidate_vessels=latest_vessels,
        destination_port=requested_port,
        cargo_tonnes=charter_request["cargo_tonnes"],
        delivery_window_days=charter_request["delivery_days"],
        waiting_vessels=port_waiting_vessels,
    )

    feasible_vessels = charter_shortlist[
        charter_shortlist["eligible"]
    ]

    if feasible_vessels.empty:
        st.error(
            "No currently tracked vessel can carry this cargo "
            "and enter the selected port."
        )

    else:
        best_vessel = feasible_vessels.iloc[0]

        with st.container(border=True):
            st.markdown("#### Recommended vessel")

            result_col_1, result_col_2, result_col_3, result_col_4 = (
                st.columns(4)
            )

            result_col_1.metric(
                "Vessel",
                best_vessel["vessel_name"],
            )

            result_col_2.metric(
                "Total arrival estimate",
                f"{best_vessel['total_arrival_days']:.1f} days",
            )

            result_col_3.metric(
                "Operational risk",
                best_vessel["risk_level"],
            )

            result_col_4.metric(
                "Recommendation score",
                f"{best_vessel['recommendation_score']}/100",
            )

            if best_vessel["within_delivery_window"]:
                st.success(
                    f"Recommendation: {best_vessel['vessel_name']} "
                    "meets the requested delivery window."
                )
            else:
                st.warning(
                    "No feasible vessel meets the requested delivery "
                    "window. The fastest feasible option is shown."
                )

            st.write(
                f"**Reason:** {best_vessel['risk_reason']}"
            )

        st.markdown("#### All vessel options")

        shortlist_columns = [
            "rank",
            "vessel_name",
            "vessel_type",
            "dwt_t",
            "capacity_margin_t",
            "port_compatible",
            "distance_to_port_nm",
            "sailing_eta_hours",
            "expected_wait_days",
            "total_arrival_days",
            "risk_level",
            "recommendation_score",
            "within_delivery_window",
            "decision",
        ]

        st.dataframe(
            charter_shortlist[shortlist_columns],
            width="stretch",
            hide_index=True,
        )


# ------------------------------------------------
# Map filters
# ------------------------------------------------

with st.sidebar:
    st.header("Map filters")

    selected_ports = st.multiselect(
        "Destination ports",
        options=ports["port_id"].tolist(),
        default=ports["port_id"].tolist()
    )

    selected_vessel_types = st.multiselect(
        "Vessel types",
        options=sorted(
            latest_vessels["vessel_type"].dropna().unique().tolist()
        ),
        default=sorted(
            latest_vessels["vessel_type"].dropna().unique().tolist()
        )
    )

    show_waiting_only = st.checkbox(
        "Show only waiting vessels",
        value=False
    )


filtered_vessels = latest_vessels[
    latest_vessels["destination"].isin(selected_ports)
    & latest_vessels["vessel_type"].isin(selected_vessel_types)
]

if show_waiting_only:
    filtered_vessels = filtered_vessels[
        filtered_vessels["status"] == "WAITING AT ANCHORAGE"
    ]


# ------------------------------------------------
# Interactive map
# ------------------------------------------------

marine_map = folium.Map(
    location=[7, 100],
    zoom_start=3,
    tiles="CartoDB positron"
)


# Add ports and anchorage zones
for port in ports.to_dict("records"):
    waiting_count = waiting_count_by_port.get(port["port_id"], 0)
    congestion = get_congestion_level(waiting_count)
    expected_wait_days = estimate_wait_days(waiting_count)

    if congestion == "High":
        port_colour = "red"
    elif congestion == "Medium":
        port_colour = "orange"
    else:
        port_colour = "green"

    port_popup = f"""
    <b>{port["name"]}, {port["country"]}</b><br>
    Maximum draft: {port["max_draft_m"]} m<br>
    Maximum DWT: {port["max_dwt_t"]:,} tonnes<br>
    Maximum LOA: {port["max_loa_m"]} m<br>
    Waiting vessels: {waiting_count}<br>
    Congestion: <b>{congestion}</b><br>
    Estimated wait: {expected_wait_days} days
    """

    folium.Marker(
        location=[port["latitude"], port["longitude"]],
        tooltip=port["name"],
        popup=folium.Popup(port_popup, max_width=300),
        icon=folium.Icon(
            color=port_colour,
            icon="anchor",
            prefix="fa"
        )
    ).add_to(marine_map)

    folium.Circle(
        location=[port["latitude"], port["longitude"]],
        radius=float(port["anchorage_radius_nm"]) * 1852,
        color=port_colour,
        fill=True,
        fill_opacity=0.08,
        tooltip=f"{port['name']} anchorage zone"
    ).add_to(marine_map)


# Add vessel markers, routes, and AIS trails
for vessel in filtered_vessels.to_dict("records"):
    destination_port = port_lookup[str(vessel["destination"])]

    marker_colour = get_marker_colour(
        vessel["status"],
        vessel["compatible"]
    )

    if vessel["eta_hours"] is None:
        eta_display = "Not available"
    else:
        eta_display = f"{vessel['eta_hours']} hours"

    if vessel["compatible"]:
        compatibility_display = "Compatible"
    else:
        compatibility_display = vessel["compatibility_issue"]

    vessel_popup = f"""
    <b>{vessel["vessel_name"]}</b><br>
    Vessel type: {vessel["vessel_type"]}<br>
    DWT: {vessel["dwt_t"]:,} tonnes<br>
    Draft: {vessel["draft_m"]} m<br>
    Current speed: {vessel["speed_knots"]} knots<br>
    Status: <b>{vessel["status"]}</b><br>
    Destination: {vessel["destination_name"]}<br>
    Distance remaining: {vessel["distance_remaining_nm"]} nm<br>
    Estimated ETA: {eta_display}<br>
    Port compatibility: <b>{compatibility_display}</b><br>
Operational risk: <b>{vessel["risk_level"]}</b><br>
Risk reason: {vessel["risk_reason"]}
    """

    folium.Marker(
        location=[vessel["latitude"], vessel["longitude"]],
        tooltip=vessel["vessel_name"],
        popup=folium.Popup(vessel_popup, max_width=320),
        icon=folium.Icon(
            color=marker_colour,
            icon="ship",
            prefix="fa"
        )
    ).add_to(marine_map)

    # Dashed planned route
    folium.PolyLine(
        locations=[
            [vessel["latitude"], vessel["longitude"]],
            [
                destination_port["latitude"],
                destination_port["longitude"]
            ]
        ],
        color=marker_colour,
        weight=2,
        opacity=0.7,
        dash_array="7, 8",
        tooltip=(
            f"{vessel['vessel_name']} → "
            f"{destination_port['name']}"
        )
    ).add_to(marine_map)

    # Solid AIS movement trail
    vessel_track = ais[
        ais["mmsi"] == str(vessel["mmsi"])
    ].sort_values("timestamp")

    if len(vessel_track) > 1:
        track_points = vessel_track[
            ["latitude", "longitude"]
        ].values.tolist()

        folium.PolyLine(
            locations=track_points,
            color="#4c78a8",
            weight=3,
            opacity=0.85,
            tooltip=f"AIS track: {vessel['vessel_name']}"
        ).add_to(marine_map)


folium.LayerControl().add_to(marine_map)


# ------------------------------------------------
# Map and result tables
# ------------------------------------------------

st.subheader("Interactive vessel map")

st.caption(
    "Blue: underway · Orange: waiting · Green: berthed · Red: port-incompatible"
)

st_folium(
    marine_map,
    width=None,
    height=650
)


st.subheader("Vessel tracking table")

display_columns = [
    "vessel_name",
    "vessel_type",
    "status",
    "destination_name",
    "speed_knots",
    "distance_remaining_nm",
    "eta_hours",
    "compatible",
    "compatibility_issue",
    "risk_level",
    "risk_score",
    "risk_reason",
]

st.dataframe(
    filtered_vessels[display_columns].sort_values("status"),
    width="stretch",
    hide_index=True
)


st.subheader("Port congestion and risk summary")

selected_port_risks = port_risk_summary[
    port_risk_summary["port_id"].isin(selected_ports)
]

st.dataframe(
    selected_port_risks[
        [
            "Port",
            "Waiting vessels",
            "Congestion",
            "Estimated wait days",
            "Operational advice"
        ]
    ],
    width="stretch",
    hide_index=True
)