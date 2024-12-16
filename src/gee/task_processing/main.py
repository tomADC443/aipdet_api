from src.gee.schemas import GeoJSONPolygonFeature
from datetime import datetime, timedelta
from src.gee.task_processing.constants import NUMBER_OF_DAYS_TEMPORAL_MAX
from src.gee.auth import authenticate
from src.gee.task_processing.preprocessing import preprocess_imagery
from shapely.geometry import Polygon
from src.gee.task_processing.image_retrieval import get_imagery
from src.gee.task_processing.utils import get_time_zone_of_center_point
from src.gee.task_processing.processing import process_collection
from pydantic import validate_call
import ee


@validate_call
def start_task_process(area_polygon_feature: GeoJSONPolygonFeature):
    """
    Function to process a GeoJSON Polygon input.

    Args:
        area_polygon_feature (dict): Input GeoJSON feature.

    Returns:
        str: Confirmation message.
    """

    end_date = datetime.now()
    start_date = end_date - timedelta(days=NUMBER_OF_DAYS_TEMPORAL_MAX)
    shapely_aoi = Polygon(area_polygon_feature.geometry.coordinates[0])

    time_zone = get_time_zone_of_center_point(shapely_aoi)

    # 1. Initialization - From here on all calculations run on GEE Servers, no local code allowed
    authenticate()
    aoi = ee.Geometry.Polygon(area_polygon_feature.geometry.coordinates)
    # 2. Get Imagery
    image_collection = get_imagery(aoi, start_date, end_date)
    # 3. Preprocessing
    preprocessed_collection = preprocess_imagery(
        image_collection, time_zone, aoi)
    # 4. Value derivation
    process_collection(preprocessed_collection)

    # 5. Prepare data export
    prepare_data_export(preprocessed_collection)

    # 6. Export data
    task = create_export_task()
    task.start()
    # Perform processing (replace this with your actual logic)
    return "Polygon input is valid and processed."
