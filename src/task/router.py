
from src.task.schemas import TaskCreationRequest
from src.dependencies import get_current_user, login_required
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.database import get_db
from src.task.models import Task
from src.task.constants import Task_Status
from fastapi.responses import JSONResponse

task_router = APIRouter()


@login_required
@task_router.post("")
def create_task(task: TaskCreationRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
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

        db.add(new_task)
        db.commit()
    except Exception as e:
        print(f"Error creating Task: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )
    # Process the AOI
    return {"message": "AOI created successfully", }
