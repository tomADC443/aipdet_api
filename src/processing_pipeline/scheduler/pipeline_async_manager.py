from sqlalchemy.orm import Session
from src.database import SessionLocal
from sqlalchemy import select, and_, update
from src.task.models import Task, TaskProcesses
from src.aoi.models import AOI
from datetime import datetime, timedelta

from src.processing_pipeline.gee.task_processing.constants import FORCED_ACTION
from src.processing_pipeline.gee.auth import authenticate
import ee
from src.task.constants import Task_Status, final_states
from src.processing_pipeline.spatial_analysis.main import get_spatial_analysis
import json
from shapely.geometry import Polygon


def pipeline_organizer():
    print("Task organizer - started")

    # Mark user tasks as completed if all gee tasks are in final state. Will run in the beginning and end of each pipeline organizer execution
    start_spatial_analysis_on_tasks_if_ready()

    db: Session = SessionLocal()
    # Get all tasks without final endstate
    openTasks = db.execute(select(Task).where(
        Task.status.notin_(final_states))).scalars().all()

    db.commit()
    print("Task organizer - Number of open tasks:", len(openTasks))
    # Check if there are any open gee_task for those tasks  (Filter according to :https://developers.google.com/earth-engine/apidocs/ee-data-getoperation )
    for task in openTasks:
        print("Task organizer - Open Task:", task.id)
        unfinished_gee_tasks = db.execute(select(TaskProcesses).where(
            TaskProcesses.task_id == task.id).filter(and_(
                TaskProcesses.gee_current_status != 'SUCCEEDED',
                TaskProcesses.gee_current_status != 'FAILED',
                TaskProcesses.gee_current_status != 'CANCELLED',
                TaskProcesses.gee_current_status != 'COMPLETED'
            ))).scalars().all()

        # Check the latest status of the unfinished gee_tasks and update the task status (forcefully end the task if it consumes too much EECUs)
        for unfinished_gee_task in unfinished_gee_tasks:
            # Check if the task is still running
            authenticate()  # init GEE access

            gee_task = ee.data.getTaskStatus(
                unfinished_gee_task.gee_task_id)[0]
            # Update the task status
            if gee_task['state'] != unfinished_gee_task.gee_current_status:
                unfinished_gee_task.gee_current_status = gee_task['state']
                unfinished_gee_task.last_updated = datetime.now()

            try:
                # Cancel task if it takes an unreasonable amount of time
                if gee_task['batch_eecu_usage_seconds'] > 300:
                    print(
                        "Task organizer - Unfinished gee task cancelled due to too many EECU used. Id:", gee_task['id'], "task status:", gee_task['state'])
                    ee.data.cancelTask(gee_task['id'])
                    unfinished_gee_task.forced_action_taken = FORCED_ACTION.Cancelled_too_many_EECU.value
                    unfinished_gee_task.last_updated = datetime.now()
            except KeyError:
                print("Task organizer - Error in checking EECU usage for task",
                      gee_task['id'], "Task might be too new to have EECU usage")

            # Cancel task if the user task (all gee tasks combined)needs to long
            if task.created_at + timedelta(hours=4) < datetime.now():
                print(
                    "Task organizer - Unfinished gee task cancelled due user task age to high. Id:", gee_task['id'], "task status:", gee_task['state'])
                ee.data.cancelTask(gee_task['id'])
                unfinished_gee_task.forced_action_taken = FORCED_ACTION.Cancelled_user_task_to_long_ago.value
                unfinished_gee_task.last_updated = datetime.now()

            db.commit()
    db.close()
    start_spatial_analysis_on_tasks_if_ready()


def start_spatial_analysis_on_tasks_if_ready():
    db: Session = SessionLocal()

    active_processes = (
        select(TaskProcesses.task_id)
        .where(TaskProcesses.gee_current_status.notin_(["SUCCEEDED", "FAILED", "CANCELLED", "COMPLETED"]))
        .distinct()
        .scalar_subquery()
    )

    # Select tasks that aren't in that set
    query = (
        select(Task, AOI.geometry)
        .join(AOI)
        .where(
            and_(
                Task.status.notin_(["Successful", "Failed"]),
                Task.id.notin_(active_processes)
            )
        )
    )
    ready_tasks_with_aois = db.execute(query).all()

    for task_with_aoi in ready_tasks_with_aois:

        task: Task = task_with_aoi[0]
        aoi = task_with_aoi[1]
        print("Task organizer - Spatial analysis started for task", task.id)
        aoi_polygon = Polygon(aoi['geometry']['coordinates'][0])
        get_spatial_analysis(str(task.id), aoi_polygon)
        # Update task status
        db.execute(update(Task).where(Task.id == task.id).values(
            status=Task_Status.Successful.value))
        db.commit()

    db.commit()
    db.close()
