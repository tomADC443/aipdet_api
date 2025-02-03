from pyproj import CRS


def get_utm_zone_from_WGS84(lon, lat):
    """
    Get UTM zone EPSG code from WGS84 coordinates

    Args:
        lon: Longitude in degrees (-180 to 180)
        lat: Latitude in degrees (-90 to 90)

    Returns:
        EPSG code for the UTM zone

    Raises:
        ValueError: If coordinates are outside valid range
    """
    if not -180 <= lon <= 180:
        raise ValueError("Longitude must be between -180 and 180 degrees")
    if not -90 <= lat <= 90:
        raise ValueError("Latitude must be between -90 and 90 degrees")

    # Handle edge case of longitude 180
    if lon == 180:
        lon = -180

    # Calculate zone number (handle zero meridian case)
    zone_number = int((lon + 180) / 6) + 1
    if lon == 0:
        zone_number = 30  # Zero meridian is in zone 30

    # Calculate EPSG code -zone number should be last2 digits
    # EPSG = 326xx for northern hemisphere
    # EPSG = 327xx for southern hemisphere
    base = 32600 if lat >= 0 else 32700
    return base + zone_number
