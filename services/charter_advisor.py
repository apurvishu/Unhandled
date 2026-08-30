import pandas as pd

from .geo_utils import (
    check_compatibility,
    estimate_wait_days,
    get_eta_hours,
    get_vessel_status,
    haversine_nm,
)
from .risk_engine import calculate_vessel_risk


def build_charter_shortlist(
    candidate_vessels,
    destination_port,
    cargo_tonnes,
    delivery_window_days,
    waiting_vessels,
):
    """
    Ranks currently tracked vessels for a new cargo requirement.

    Prototype assumption:
    DWT is used as maximum cargo-carrying capacity.
    """

    rows = []

    for vessel in candidate_vessels.to_dict("records"):
        distance_nm = haversine_nm(
            vessel["latitude"],
            vessel["longitude"],
            destination_port["latitude"],
            destination_port["longitude"],
        )

        status = get_vessel_status(
            distance_nm,
            vessel["speed_knots"],
            destination_port["anchorage_radius_nm"],
        )

        sailing_eta_hours = get_eta_hours(
            distance_nm,
            vessel["speed_knots"],
        )

        port_compatible, compatibility_issue = check_compatibility(
            vessel,
            destination_port,
        )

        cargo_sufficient = vessel["dwt_t"] >= cargo_tonnes
        capacity_margin_t = vessel["dwt_t"] - cargo_tonnes
        expected_wait_days = estimate_wait_days(waiting_vessels)

        if sailing_eta_hours is None:
            total_arrival_days = None
        else:
            total_arrival_days = round(
                (sailing_eta_hours / 24) + expected_wait_days,
                2,
            )

        if not port_compatible:
            risk_score = 100
            risk_level = "High"
            risk_reason = compatibility_issue

        elif not cargo_sufficient:
            risk_score = 100
            risk_level = "High"
            risk_reason = "Vessel DWT is below required cargo quantity"

        else:
            risk_input = vessel.copy()
            risk_input["compatible"] = port_compatible
            risk_input["status"] = status
            risk_input["eta_hours"] = sailing_eta_hours

            risk_score, risk_level, risk_reason = calculate_vessel_risk(
                risk_input,
                waiting_vessels,
            )

        eligible = (
            port_compatible
            and cargo_sufficient
            and total_arrival_days is not None
        )

        if eligible:
            risk_penalty = {
                "Low": 0,
                "Medium": 20,
                "High": 45,
            }[risk_level]

            arrival_penalty = min(total_arrival_days * 4, 45)
            capacity_penalty = min(
                (capacity_margin_t / cargo_tonnes) * 4,
                10,
            )

            recommendation_score = round(
                max(
                    0,
                    100
                    - risk_penalty
                    - arrival_penalty
                    - capacity_penalty,
                ),
                1,
            )

            within_delivery_window = (
                total_arrival_days <= delivery_window_days
            )

            if within_delivery_window:
                decision = "Recommended"
            else:
                decision = "Feasible, but late for requested delivery"

        else:
            recommendation_score = 0
            within_delivery_window = False
            decision = "Not eligible"

        rows.append(
            {
                "vessel_name": vessel["vessel_name"],
                "vessel_type": vessel["vessel_type"],
                "dwt_t": vessel["dwt_t"],
                "capacity_margin_t": capacity_margin_t,
                "port_compatible": port_compatible,
                "status_at_selected_port": status,
                "distance_to_port_nm": distance_nm,
                "sailing_eta_hours": sailing_eta_hours,
                "expected_wait_days": expected_wait_days,
                "total_arrival_days": total_arrival_days,
                "risk_level": risk_level,
                "risk_reason": risk_reason,
                "recommendation_score": recommendation_score,
                "within_delivery_window": within_delivery_window,
                "eligible": eligible,
                "decision": decision,
            }
        )

    shortlist = pd.DataFrame(rows)

    if shortlist.empty:
        return shortlist

    shortlist = shortlist.sort_values(
        [
            "eligible",
            "within_delivery_window",
            "recommendation_score",
            "total_arrival_days",
        ],
        ascending=[False, False, False, True],
        na_position="last",
    ).reset_index(drop=True)

    shortlist.insert(0, "rank", range(1, len(shortlist) + 1))

    return shortlist