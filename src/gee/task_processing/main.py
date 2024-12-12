from src.gee.schemas import PolygonInputSchema
from datetime import datetime, timedelta
from src.gee.task_processing.constants import NUMBER_OF_YEARS_TEMPORAL_MAX
from src.gee.auth import authenticate
from src.gee.task_processing.preprocessing import preprocess_imagery
import ee
from src.gee.task_processing.image_retrieval import get_imagery
from src.gee.task_processing.utils import get_time_zone_of_center_point
from src.gee.task_processing.preprocessing import process_collection


def start_task_process(area_polygon_feature: PolygonInputSchema):
    """
    Function to process a GeoJSON Polygon input.

    Args:
        area_polygon_feature (dict): Input GeoJSON feature.

    Returns:
        str: Confirmation message.
    """
    # Validate input using Pydantic schema
    validated_data = PolygonInputSchema(**area_polygon_feature)

    end_date = datetime.now()
    start_date = end_date - timedelta(years=NUMBER_OF_YEARS_TEMPORAL_MAX)
    aoi = ee.Geometry.Polygon(validated_data.coordinates, start_date, end_date)
    time_zone = get_time_zone_of_center_point(validated_data.coordinates)

    # 1. Initialization - From here on all calculations run on GEE Servers, no local code allowed
    authenticate()
    # 2. Get Imagery
    image_collection = get_imagery(aoi, start_date, end_date)
    # 3. Preprocessing
    preprocessed_collection = preprocess_imagery(image_collection, time_zone)
    # 4. Value derivation
    process_collection(preprocessed_collection)
    # 5. Data Export

    # Perform processing (replace this with your actual logic)
    return "Polygon input is valid and processed."
