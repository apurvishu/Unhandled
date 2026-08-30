from services.geo_utils import (
    haversine_nm,
    get_eta_hours,
    get_vessel_status,
    check_compatibility,
    get_congestion_level,
    estimate_wait_days
)


# Test 1: Same location should have zero distance
distance = haversine_nm(20.26, 86.67, 20.26, 86.67)
print("Same-location distance:", distance, "nm")


# Test 2: Vessel status
print("Status 1:", get_vessel_status(10, 0.5, 15))
print("Status 2:", get_vessel_status(120, 11, 15))
print("Status 3:", get_vessel_status(1, 0.4, 15))


# Test 3: ETA
print("ETA:", get_eta_hours(240, 12), "hours")


# Test 4: Compatibility
vessel = {
    "draft_m": 13.8,
    "dwt_t": 76000,
    "loa_m": 225
}

port = {
    "max_draft_m": 17.1,
    "max_dwt_t": 125000,
    "max_loa_m": 290
}

compatible, reason = check_compatibility(vessel, port)

print("Compatible:", compatible)
print("Reason:", reason)


# Test 5: Congestion
print("Congestion:", get_congestion_level(4))
print("Estimated wait:", estimate_wait_days(4), "days")