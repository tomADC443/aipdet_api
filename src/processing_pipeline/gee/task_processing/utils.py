import ee
from timezonefinder import TimezoneFinder
from shapely.geometry import Polygon
from src.gee.task_processing.exceptions import TimezoneRetrievalError
from src.gee.task_processing.constants import S
tf = TimezoneFinder()


def get_time_zone_of_center_point(aoi: Polygon) -> str:

    centroid = aoi.centroid
    time_zone = tf.timezone_at(lng=centroid.x, lat=centroid.y)
    if time_zone:
        return time_zone

    raise TimezoneRetrievalError(location=f"lng={centroid.x} lat={centroid.y}")


def calculate_masked_percentage(image, region):
    # Get total pixel count
    total_pixels = image.mask().reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=region,
        scale=10
    ).get('constant')
    print(total_pixels.getInfo())
    # Get unmasked pixel count
    unmasked_pixels = image.mask().gt(0).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=region,
        scale=10
    ).get('constant')

    # Calculate percentage
    masked_percentage = ee.Number(1).subtract(
        ee.Number(unmasked_pixels).divide(total_pixels)
    ).multiply(100)

    return masked_percentage


def enforce_polygon(feature: ee.Feature) -> ee.Feature:
    geom = feature.geometry()
    polygon = geom.buffer(1).simplify(1)
    return feature.setGeometry(polygon)


def swallow_by_buffer(feature: ee.Feature) -> ee.Feature:
    geom = feature.geometry()
    # buffer out
    geom = geom.buffer(6).simplify(ee.ErrorMargin(
        5, S["TOLERANCE_UNIT"]))  # type: ignore
    # buffer back in
    geom = geom.buffer(-6).simplify(ee.ErrorMargin(
        20, S["TOLERANCE_UNIT"]))  # type: ignore
    # dissolve overhead
    return feature.setGeometry(geom.dissolve())


def extract_polygons_from_geometry(feature: ee.Feature) -> ee.Feature:
    # Get the geometry
    geom = feature.geometry()

    # If it's a GeometryCollection, extract just the polygons/multipolygons
    # and merge them into a single MultiPolygon
    polygons = geom.geometries().filter(
        ee.Filter.Or(
            ee.Filter.eq('type', 'Polygon'),
            ee.Filter.eq('type', 'MultiPolygon')
        )
    )

    # Create a new MultiPolygon from the filtered geometries
    new_geom = ee.Geometry.MultiPolygon(polygons)

    return feature.setGeometry(new_geom)
