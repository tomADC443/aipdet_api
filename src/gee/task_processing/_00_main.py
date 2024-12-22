from datetime import datetime, timedelta
from src.gee.task_processing.constants import NUMBER_OF_DAYS_TEMPORAL_MAX
from src.gee.auth import authenticate
from src.gee.task_processing._01_preprocessing import preprocess_imagery
from shapely.geometry import Polygon
from src.gee.task_processing.image_retrieval import get_imagery
from src.gee.task_processing.utils import get_time_zone_of_center_point
from src.gee.task_processing._02_processing import process_collection
from src.gee.task_processing._03_prepare_export import prepare_export
from src.gee.task_processing._04_export import start_export
import ee
from src.gee.task_processing.metadata import GeeTaskProcessingMetadata


def start_task_process(shapely_aoi_polygon: Polygon, metadata: GeeTaskProcessingMetadata):
    """
    Function to process a GeoJSON Polygon input.

    Args:
        area_polygon_feature (dict): Input GeoJSON feature.

    Returns:
        str: Confirmation message.
    """

    coordinates = list(shapely_aoi_polygon.exterior.coords)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=NUMBER_OF_DAYS_TEMPORAL_MAX)
    metadata.time_zone = get_time_zone_of_center_point(shapely_aoi_polygon)
    # 1. Initialization - From here on all calculations run on GEE Servers, no local code allowed
    authenticate()
    aoi = ee.Geometry.Polygon(coordinates)
    # 2. Get Imagery
    image_collection = get_imagery(aoi, start_date, end_date)
    # 3. Preprocessing
    preprocessed_collection = preprocess_imagery(
        image_collection, aoi, metadata)
    # 4. Value derivation

    feature_collection = process_collection(preprocessed_collection, aoi)

    # 5. Prepare data export
    featureCollection = prepare_export(feature_collection)

    # 6. Export data
    start_export(featureCollection)
    # Perform processing (replace this with your actual logic)
    return "Polygon input is valid and processed."
