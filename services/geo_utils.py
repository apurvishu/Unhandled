from math import radians, sin, cos, sqrt, atan2


def haversine_nm(lat1, lon1, lat2, lon2):
    """
    Finds straight-line distance between two latitude/longitude points.
    Result is returned in nautical miles.
    """

    earth_radius_km = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    distance_km = 2 * earth_radius_km * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return round(distance_km / 1.852, 2)


def get_eta_hours(distance_nm, speed_knots):
    """
    Calculates estimated arrival time in hours.
    ETA = distance ÷ speed.
    """

    if speed_knots <= 0:
        return None

    return round(distance_nm / speed_knots, 1)


def get_vessel_status(distance_nm, speed_knots, anchorage_radius_nm):
    """
    Identifies whether a vessel is sailing, waiting, or berthed.
    """

    # Vessel is very close to port and nearly stationary
    if distance_nm <= 2 and speed_knots <= 1:
        return "BERTHED"

    # Vessel is near port, inside anchorage area, and almost stationary
    if distance_nm <= anchorage_radius_nm and speed_knots <= 2:
        return "WAITING AT ANCHORAGE"

    # Vessel is moving or far from the port
    return "UNDERWAY"


def check_compatibility(vessel, port):
    """
    Checks whether a vessel can enter a port.
    Vessel and port are dictionaries.
    """

    issues = []

    if vessel["draft_m"] > port["max_draft_m"]:
        issues.append("Draft exceeds port limit")

    if vessel["dwt_t"] > port["max_dwt_t"]:
        issues.append("DWT exceeds port limit")

    if vessel["loa_m"] > port["max_loa_m"]:
        issues.append("Length exceeds port limit")

    compatible = len(issues) == 0

    return compatible, ", ".join(issues)


def get_congestion_level(waiting_vessels):
    """
    Converts number of waiting vessels into a congestion category.
    """

    if waiting_vessels >= 6:
        return "High"

    if waiting_vessels >= 3:
        return "Medium"

    return "Low"


def estimate_wait_days(waiting_vessels):
    """
    Prototype rule:
    Every waiting vessel adds approximately half a day of waiting time.
    """

    return round(waiting_vessels * 0.5, 1)