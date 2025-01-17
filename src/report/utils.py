from pyproj import CRS


from pyproj import CRS


def get_utm_zone_from_WGS84(lon, lat):
    # find zone (every 6 degrees is one UTM zone)
    zone_number = int((lon + 180) / 6) + 1

    # Determine if north or south hemisphere
    hemisphere = 'north' if lat >= 0 else 'south'

    # Create UTM CRS string
    utm = CRS.from_dict({
        'proj': 'utm',
        'zone': zone_number,
        'hemisphere': hemisphere,
        'ellps': 'WGS84'
    })

    return utm.to_epsg()
