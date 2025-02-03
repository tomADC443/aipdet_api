from src.task.schemas import TaskCreationRequest, TaskDeletionRequest
from src.dependencies import get_current_user, login_required
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from src.database import get_db
from src.task.models import Task, TaskProcesses
from src.task.constants import Task_Status
from fastapi.responses import JSONResponse
from src.aoi.models import AOI
from shapely.geometry import Polygon
from src.processing_pipeline.gee.task_processing.metadata import GeeTaskProcessingMetadata
from src.processing_pipeline.gee.task_processing.main import start_task_process
from src.report.utils import execute_safe_query
from src.config import get_settings
settings = get_settings()

task_router = APIRouter()
tasks_router = APIRouter()


@login_required
@task_router.delete("")
def delete_task(data: TaskDeletionRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    user_id = current_user['sub']
    try:
        task = db.execute(
            select(Task).where(Task.user_id == user_id).where(Task.id == data.id)).scalars().first()

        if not task:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "Task not found or you don't have permission to delete it."}
            )

        if str(task.status) != Task_Status.Successful.value and str(task.status) != Task_Status.Failed.value:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Task cannot be deleted because it is still processing."}
            )

        db.execute(
            delete(TaskProcesses).where(TaskProcesses.task_id == data.id))

        # Delete from bigQuery
        query = """
            DELETE FROM `{table}` WHERE process_id = @task_id;
        """.format(table=settings.DATABASE_GRID_TABLE)

        execute_safe_query(
            query=query,
            params={"task_id": data.id}
        )
        query = """
            DELETE FROM `{table}` WHERE process_id = @task_id;
        """.format(table=settings.DATABASE_REPORT_TABLE)

        execute_safe_query(
            query=query,
            params={"task_id": data.id}
        )

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    finally:
        db.close()
    return


@ login_required
@ tasks_router.get("")
def get_tasks(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    user_id = current_user['sub']
    tasks = db.execute(
        select(Task, AOI).join(AOI, Task.aoi_id == AOI.id).where(Task.user_id == user_id)).unique().all()

    responseData = [
        {
            "id": str(task.id),
            "name": task.name,
            "status": task.status,
            "createdAt": int(task.created_at.timestamp()),
            "isPublic": task.is_public,
            "aoi": {
                "id": str(aoi.id),
                "name": aoi.name,
                "description": aoi.description,
                "geometry": aoi.geometry,
                "createdAt": int(aoi.created_at.timestamp()),
            }
        } for task, aoi in tasks
    ]
    return responseData


@ login_required
@ tasks_router.get("/public")
def get_public_tasks(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    user_id = current_user['sub']
    tasks = db.execute(
        select(Task, AOI).join(AOI, Task.aoi_id == AOI.id).where(Task.user_id != user_id).where(Task.is_public == True)).unique().all()

    responseData = [
        {
            "id": str(task.id),
            "name": task.name,
            "status": task.status,
            "createdAt": int(task.created_at.timestamp()),
            "isPublic": task.is_public,
            "aoi": {
                "id": str(aoi.id),
                "name": aoi.name,
                "description": aoi.description,
                "geometry": aoi.geometry,
                "createdAt": int(aoi.created_at.timestamp()),
            }
        } for task, aoi in tasks
    ]
    return responseData


@ login_required
@ task_router.post("")
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

        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        aoi_polygon = Polygon(aoi.geometry['geometry']['coordinates'][0])

        metadata = GeeTaskProcessingMetadata(
            task_id=str(new_task.id), user_id=str(new_task.user_id), aoi_id=str(new_task.aoi_id))

        def process_task_wrapper():
            import asyncio
            asyncio.run(start_task_process(aoi_polygon, metadata))

        background_task.add_task(process_task_wrapper)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Task created successfully. Processing started."}
        )

    except Exception as e:
        print(f"Error creating Task: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )
    # Process the AOI
