import pandas as pd

from .geo_utils import haversine_nm


def move_toward_destination(
    latitude,
    longitude,
    destination_latitude,
    destination_longitude,
    travel_distance_nm
):
    """
    Moves a vessel towards its destination.
    This is a simple hackathon simulation, not an exact sea-route calculation.
    """

    distance_remaining_nm = haversine_nm(
        latitude,
        longitude,
        destination_latitude,
        destination_longitude
    )

    if distance_remaining_nm == 0:
        return latitude, longitude

    movement_fraction = min(
        travel_distance_nm / distance_remaining_nm,
        1
    )

    new_latitude = latitude + (
        destination_latitude - latitude
    ) * movement_fraction

    new_longitude = longitude + (
        destination_longitude - longitude
    ) * movement_fraction

    return new_latitude, new_longitude


def advance_ais_positions(
    ais_positions,
    port_lookup,
    virtual_hours=6
):
    """
    Creates one new AIS position for every vessel.

    Each simulator tick represents a chosen number of virtual hours.
    Vessels sailing at sea move toward destination.
    Vessels inside the anchorage zone slow down and wait.
    """

    updated_positions = ais_positions.copy()
    updated_positions["timestamp"] = pd.to_datetime(
        updated_positions["timestamp"]
    )

    new_rows = []

    for _, vessel_track in updated_positions.groupby("mmsi"):
        current_position = (
            vessel_track
            .sort_values("timestamp")
            .iloc[-1]
            .copy()
        )

        destination_id = str(current_position["destination"])
        destination_port = port_lookup.get(destination_id)

        # Skip a vessel if the destination port is unknown
        if destination_port is None:
            continue

        next_position = current_position.copy()

        # Advance virtual time
        next_position["timestamp"] = (
            current_position["timestamp"]
            + pd.Timedelta(hours=virtual_hours)
        )

        distance_to_port_nm = haversine_nm(
            current_position["latitude"],
            current_position["longitude"],
            destination_port["latitude"],
            destination_port["longitude"]
        )

        anchorage_radius_nm = float(
            destination_port["anchorage_radius_nm"]
        )

        # Vessel has reached berth
        if distance_to_port_nm <= 2:
            next_position["speed_knots"] = 0.3

        # Vessel has reached anchorage and is waiting
        elif distance_to_port_nm <= anchorage_radius_nm:
            next_position["speed_knots"] = 0.5

        # Vessel is travelling towards destination
        else:
            speed_knots = float(
                current_position["speed_knots"]
            )

            distance_to_travel_nm = (
                speed_knots * virtual_hours
            )

            new_latitude, new_longitude = move_toward_destination(
                current_position["latitude"],
                current_position["longitude"],
                destination_port["latitude"],
                destination_port["longitude"],
                distance_to_travel_nm
            )

            next_position["latitude"] = new_latitude
            next_position["longitude"] = new_longitude

            # Slow vessel when it reaches the port area
            if distance_to_travel_nm >= distance_to_port_nm:
                next_position["speed_knots"] = 0.5

        new_rows.append(next_position)

    new_positions = pd.DataFrame(new_rows)

    return pd.concat(
        [updated_positions, new_positions],
        ignore_index=True
    )