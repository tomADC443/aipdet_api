from datetime import datetime, timedelta
from src.gee.task_processing.constants import NUMBER_OF_DAYS_TEMPORAL_MAX
from src.gee.auth import authenticate
from src.gee.task_processing._01_preprocessing import preprocess_imagery
from shapely.geometry import Polygon
from src.gee.task_processing.image_retrieval import get_imagery, get_date_ranges
from src.gee.task_processing.utils import get_time_zone_of_center_point
from src.gee.task_processing._02_processing import process_collection
from src.gee.task_processing._03_prepare_export import prepare_export
from src.gee.task_processing._04_export import start_export
import ee
from src.gee.task_processing.metadata import GeeTaskProcessingMetadata
from src.gee.task_processing.monitoring import monitor_tasks
from src.database import get_db
from sqlalchemy import select
from src.task.models import Task
from src.task.constants import Task_Status
from sqlalchemy.orm import Session
from src.database import SessionLocal


async def start_task_process(shapely_aoi_polygon: Polygon, metadata: GeeTaskProcessingMetadata):

    coordinates = list(shapely_aoi_polygon.exterior.coords)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=NUMBER_OF_DAYS_TEMPORAL_MAX)
    metadata.time_zone = get_time_zone_of_center_point(shapely_aoi_polygon)
    # 1. Initialization - From here on all calculations run on GEE Servers, no local code allowed
    authenticate()

    aoi = ee.Geometry.Polygon(coordinates)
    image_ranges = get_date_ranges(
        aoi, int(start_date.timestamp() * 1000), int(end_date.timestamp() * 1000), timezone=metadata.time_zone)
    print(metadata.time_zone)
    tasks = []
    for range in image_ranges:

        # 2. Get Imagery
        image_collection = get_imagery(
            aoi, range["start_date"], range["end_date"])
        # 3. Preprocessing
        preprocessed_collection = preprocess_imagery(
            image_collection, aoi, metadata)
        # 4. Value derivation (Processing)

        feature_collection = process_collection(
            preprocessed_collection, aoi)

        # 5. Prepare data export
        featureCollection = prepare_export(feature_collection, metadata)

        # 6. Export data
        task = start_export(featureCollection, metadata)
        tasks.append(task)
        # Perform processing (replace this with your actual logic)

    await monitor_tasks(tasks, job_id=metadata.task_id)
    db: Session = SessionLocal()
    # Update task status to completed
    task = db.execute(
        select(Task).where(Task.id == metadata.task_id)).scalar()
    task.status = Task_Status.Successful.value
    db.commit()
    db.close()
    return
