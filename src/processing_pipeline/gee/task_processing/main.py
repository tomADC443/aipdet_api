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
from sqlalchemy import select
from src.task.models import Task, TaskProcesses
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
        preprocessed_image = preprocess_imagery(
            image_collection, aoi, metadata)
        # 4. Value derivation (Processing)

        feature_collection = process_collection(
            preprocessed_image, aoi)

        # 5. Prepare data export
        featureCollection = prepare_export(
            feature_collection, metadata, preprocessed_image)

        # 6. Export data
        started_task = start_export(featureCollection, metadata)
        tasks.append(started_task)
        # Perform processing (replace this with your actual logic)

    task_processes = [
        TaskProcesses(

            task_id=metadata.task_id,
            gee_task_id=task.status()["id"],
            gee_current_status=task.status()["state"],
            last_updated=datetime.now()
        ) for task in tasks
    ]

    db: Session = SessionLocal()
    db.add_all(task_processes)
    db.commit()

    # Update task status to completed
    userTask = db.execute(select(Task).where(
        Task.id == metadata.task_id)).scalar()
    if userTask:
        userTask.status = Task_Status.Processing.value  # type: ignore
    else:
        raise Exception("User task not found!" + metadata.task_id)
    db.commit()
    db.close()
    return
