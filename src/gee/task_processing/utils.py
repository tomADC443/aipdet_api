from src.gee.schemas import PolygonInputSchema
from timezonefinder import TimezoneFinder
from shapely.geometry import Polygon
from src.gee.task_processing.exceptions import TimezoneRetrievalError
tf = TimezoneFinder()


def get_time_zone_of_center_point(aoi: PolygonInputSchema) -> str:

    shapely_polygon = Polygon(aoi.coordinates)
    centroid = shapely_polygon.centroid
    time_zone = tf.timezone_at(lng=centroid.x, lat=centroid.y)
    if time_zone:
        return time_zone

    raise TimezoneRetrievalError(location=f"lng={centroid.x} lat={centroid.y}")
