import pandas as pd

from .geo_utils import get_congestion_level, estimate_wait_days


def calculate_vessel_risk(vessel, waiting_vessels):
    """
    Returns a risk score, risk level, and simple operational reason
    for one vessel.
    """

    # A vessel that cannot use its destination port is always high risk.
    if not vessel["compatible"]:
        return 100, "High", "Vessel exceeds one or more port limits"

    # A vessel already at berth has no arrival-delay risk.
    if vessel["status"] == "BERTHED":
        return 0, "Low", "Vessel is berthed"

    congestion = get_congestion_level(waiting_vessels)

    score = 0
    reasons = []

    if congestion == "Medium":
        score += 30
        reasons.append("Moderate port congestion")

    elif congestion == "High":
        score += 55
        reasons.append("High port congestion")

    if vessel["status"] == "WAITING AT ANCHORAGE":
        score += 35
        reasons.append("Vessel is already waiting at anchorage")

    eta_hours = vessel.get("eta_hours")

    if (
        pd.notna(eta_hours)
        and eta_hours <= 24
        and congestion != "Low"
    ):
        score += 15
        reasons.append("Arrival expected within 24 hours")

    if score >= 60:
        risk_level = "High"
    elif score >= 30:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    if not reasons:
        reasons.append("Compatible vessel and no major congestion")

    return score, risk_level, "; ".join(reasons)


def add_risk_to_vessels(vessels, waiting_count_by_port):
    """
    Adds risk_score, risk_level, and risk_reason columns
    to the vessel tracking DataFrame.
    """

    risk_rows = []

    for vessel in vessels.to_dict("records"):
        destination_id = str(vessel["destination"])
        waiting_vessels = waiting_count_by_port.get(destination_id, 0)

        score, level, reason = calculate_vessel_risk(
            vessel,
            waiting_vessels
        )

        risk_rows.append({
            "risk_score": score,
            "risk_level": level,
            "risk_reason": reason
        })

    risk_data = pd.DataFrame(risk_rows)

    return pd.concat(
        [
            vessels.reset_index(drop=True),
            risk_data
        ],
        axis=1
    )


def build_port_risk_summary(ports, waiting_count_by_port):
    """
    Creates a port-level congestion and operational-advice table.
    """

    summary_rows = []

    for port in ports.to_dict("records"):
        port_id = str(port["port_id"])
        waiting_vessels = waiting_count_by_port.get(port_id, 0)

        congestion = get_congestion_level(waiting_vessels)
        wait_days = estimate_wait_days(waiting_vessels)

        if congestion == "High":
            advice = (
                "High delay risk — consider waiting or using another port"
            )
        elif congestion == "Medium":
            advice = (
                "Moderate delay risk — include waiting time in planning"
            )
        else:
            advice = "Port is operating normally"

        summary_rows.append({
            "port_id": port_id,
            "Port": port["name"],
            "Waiting vessels": waiting_vessels,
            "Congestion": congestion,
            "Estimated wait days": wait_days,
            "Operational advice": advice
        })

    return pd.DataFrame(summary_rows)