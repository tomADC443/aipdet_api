import pytest
from src.processing_pipeline.spatial_analysis.utils import get_utm_zone_from_WGS84


def test_amsterdam_coordinates():
    """Test UTM zone calculation for Amsterdam (Zone 31N)"""
    lon, lat = 4.9, 52.37  # Amsterdam coordinates
    utm_code = get_utm_zone_from_WGS84(lon, lat)
    assert utm_code == 32631  # EPSG code for UTM zone 31N


def test_new_york_coordinates():
    """Test UTM zone calculation for New York (Zone 18N)"""
    lon, lat = -74.0, 40.7  # New York coordinates
    utm_code = get_utm_zone_from_WGS84(lon, lat)
    assert utm_code == 32618  # EPSG code for UTM zone 18N


def test_sydney_coordinates():
    """Test UTM zone calculation for Sydney (Zone 56S)"""
    lon, lat = 151.2, -33.9  # Sydney coordinates
    utm_code = get_utm_zone_from_WGS84(lon, lat)
    assert utm_code == 32756  # EPSG code for UTM zone 56S


def test_zero_meridian():
    """Test UTM zone calculation at the Prime Meridian"""
    # Greenwich, London is exactly on the prime meridian
    lon, lat = 0.0, 51.5
    utm_code = get_utm_zone_from_WGS84(lon, lat)
    assert utm_code == 32630  # EPSG code for UTM zone 30N


def test_edge_cases():
    """Test UTM zone calculation at edge cases"""
    # International Date Line (180° longitude)
    assert get_utm_zone_from_WGS84(
        180.0, 0.0) == 32601  # Should wrap to zone 1
    assert get_utm_zone_from_WGS84(-180.0, 0.0) == 32601  # Zone 1


def test_equator_crossing():
    """Test UTM zone calculation near the equator"""
    # Just north of equator
    utm_code_north = get_utm_zone_from_WGS84(15.0, 0.1)
    assert utm_code_north == 32633  # EPSG code for UTM zone 33N

    # Just south of equator
    utm_code_south = get_utm_zone_from_WGS84(15.0, -0.1)
    assert utm_code_south == 32733  # EPSG code for UTM zone 33S


def test_invalid_longitude():
    """Test handling of invalid longitude values"""
    with pytest.raises(ValueError, match="Longitude must be between -180 and 180 degrees"):
        get_utm_zone_from_WGS84(181.0, 0.0)

    with pytest.raises(ValueError, match="Longitude must be between -180 and 180 degrees"):
        get_utm_zone_from_WGS84(-181.0, 0.0)


def test_invalid_latitude():
    """Test handling of invalid latitude values"""
    with pytest.raises(ValueError, match="Latitude must be between -90 and 90 degrees"):
        get_utm_zone_from_WGS84(0.0, 91.0)

    with pytest.raises(ValueError, match="Latitude must be between -90 and 90 degrees"):
        get_utm_zone_from_WGS84(0.0, -91.0)


@pytest.mark.parametrize("lon,lat,expected_zone", [
    (0.0, 0.0, 32630),    # Zone 30N (Prime Meridian)
    (3.0, 0.0, 32631),    # Zone 31N
    (-9.0, 0.0, 32629),   # Zone 29N
    (15.0, 0.0, 32633),   # Zone 33N
    (177.0, 0.0, 32660)   # Zone 60N
])
def test_multiple_zones(lon, lat, expected_zone):
    """Test UTM zone calculation for multiple coordinates"""
    utm_code = get_utm_zone_from_WGS84(lon, lat)
    assert utm_code == expected_zone
