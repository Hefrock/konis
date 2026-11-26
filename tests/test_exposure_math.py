import math

import pytest

from konis.geo import angular_difference, bearing_deg, haversine_km


def test_haversine_known_distance():
    # One degree of latitude ~ 111.19 km on the mean sphere
    assert haversine_km(40, -91, 41, -91) == pytest.approx(111.195, abs=0.01)
    assert haversine_km(40.79, -91.24, 40.79, -91.24) == 0


@pytest.mark.parametrize("lat2,lon2,expected", [
    (41.79, -91.2447, 0.0), (40.7906, -90.0, 90.0), (39.79, -91.2447, 180.0),
    (40.7906, -92.5, 270.0)])
def test_bearing_cardinal(lat2, lon2, expected):
    b = bearing_deg(40.7906, -91.2447, lat2, lon2)
    assert angular_difference(b, expected) < 1.0


@pytest.mark.parametrize("a,b,d", [(359, 1, 2), (1, 359, 2), (0, 180, 180), (90, 270, 180),
                                   (10, 10, 0), (720, 0, 0), (-10, 10, 20)])
def test_angular_difference_wraps(a, b, d):
    assert angular_difference(a, b) == pytest.approx(d)


def test_bearing_range():
    for lon in range(-180, 180, 7):
        assert 0 <= bearing_deg(0, 0, 10, lon) < 360 or math.isclose(lon, 0)
