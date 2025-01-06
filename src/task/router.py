
import json
from src.task.schemas import TaskCreationRequest
from src.dependencies import get_current_user, login_required
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from src.database import get_db
from src.task.models import Task
from src.task.constants import Task_Status
from fastapi.responses import JSONResponse
from src.aoi.models import AOI
from shapely.geometry import Polygon
from src.gee.task_processing.metadata import GeeTaskProcessingMetadata
from src.gee.task_processing._00_main import start_task_process
task_router = APIRouter()


@login_required
@task_router.post("")
def create_task(background_task: BackgroundTasks, task: TaskCreationRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
        Handles Task creation requests.
        Validates input data and saves the Task to the database.
        Starts Task processing automatically.
        Returns success or error response.
        """
    try:

        # Create a new AOI instance
        new_task = Task(
            user_id=current_user['sub'],
            aoi_id=task.aoiId,
            name=task.name,
            status=Task_Status.Processing.value,
            is_public=task.isPublic
        )

        aoi = db.execute(
            select(AOI).where(AOI.id == new_task.aoi_id)).scalar()

        if not aoi:
            return JSONResponse(
                status_code=404,
                content={"detail": "AOI not found."}
            )

        aoi_polygon = Polygon(aoi.geometry['geometry']['coordinates'][0])

        metadata = GeeTaskProcessingMetadata(
            task_id=str(new_task.id), user_id=str(new_task.user_id), aoi_id=str(new_task.aoi_id))

        db.add(new_task)
        db.commit()

        background_task.add_task(start_task_process, aoi_polygon, metadata)
        return JSONResponse(
            status_code=200,
            content={"message": "Task created successfully. Processing started."}
        )

    except Exception as e:
        print(f"Error creating Task: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )
    # Process the AOI
