from konis.reference.openaq_coverage import rows


def test_rows_filters_by_radius_and_sorts():
    locs = [
        {"id": 1, "name": "far", "coordinates": {"latitude": 41.9, "longitude": -91.27}},
        {"id": 2, "name": "near", "isMonitor": False, "provider": {"name": "PurpleAir"},
         "coordinates": {"latitude": 40.70, "longitude": -91.40},
         "sensors": [{"parameter": {"name": "pm25"}}, {"parameter": {"name": "pm10"}}]},
        {"id": 3, "name": "nocoords", "coordinates": {}},
    ]
    (r,) = rows(locs)
    assert r["openaq_id"] == 2 and r["parameters"] == "pm10;pm25" and r["distance_km"] < 20
    assert 180 < r["bearing_deg"] < 270   # south-west of the origin
