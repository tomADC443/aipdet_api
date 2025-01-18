from sqlalchemy.orm import Session
from src.database import SessionLocal
from sqlalchemy import select, and_, update
from src.task.models import Task, TaskProcesses
import datetime
from src.processing_pipeline.gee.task_processing.constants import FORCED_ACTION
from src.processing_pipeline.gee.auth import authenticate
import ee
from src.task.constants import Task_Status, final_states


def pipeline_organizer():

    # Mark user tasks as completed if all gee tasks are in final state. Will run in the beginning and end of each pipeline organizer execution
    cleanup_tasks()

    db: Session = SessionLocal()
    # Get all tasks without final endstate
    openTasks = db.execute(select(Task).where(
        Task.status.notin_(final_states))).all()

    db.commit()

    # Check if there are any open gee_task for those tasks  (Filter according to :https://developers.google.com/earth-engine/apidocs/ee-data-getoperation )
    for task in openTasks:

        unfinished_gee_tasks = db.execute(select(TaskProcesses).where(
            TaskProcesses.task_id == task.id).filter(and_(
                TaskProcesses.gee_current_status != 'SUCCEEDED',
                TaskProcesses.gee_current_status != 'FAILED',
                TaskProcesses.gee_current_status != 'CANCELLED',
            ))).all()

        # Check the latest status of the unfinished gee_tasks and update the task status (forcefully end the task if it consumes too much EECUs)
        for unfinished_gee_task in unfinished_gee_tasks:
            # Check if the task is still running
            authenticate()  # init GEE access
            gee_task = ee.data.getTaskStatus(TaskProcesses.task_id)[0]
            # Update the task status
            if gee_task['state'] != unfinished_gee_task.gee_current_status:
                unfinished_gee_task.gee_current_status = gee_task['state']
                unfinished_gee_task.last_updated = datetime.now()

            # Cancel task if it takes an unreasonable amount of time
            if gee_task['batch_eecu_usage_seconds'] > 300:
                ee.data.cancelTask(gee_task['id'])
                unfinished_gee_task.forced_action_taken = FORCED_ACTION.Cancelled_to_many_EECU.value
                unfinished_gee_task.last_updated = datetime.now()

            # Cancel task if the user task (all gee tasks combined)needs to long
            if task.created_at + datetime.timedelta(hours=4) < datetime.now():
                ee.data.cancelTask(gee_task['id'])
                unfinished_gee_task.forced_action_taken = FORCED_ACTION.Cancelled_to_many_EECU.value
                unfinished_gee_task.last_updated = datetime.now()

            db.commit()
    db.close()
    cleanup_tasks()


def cleanup_tasks():
    db: Session = SessionLocal()

    # Subquery to check all related TaskProcesses for the wanted states
    task_process_check = select(TaskProcesses.task_id).where(
        TaskProcesses.gee_current_status.notin_(
            ["SUCCEEDED", "FAILED", "CANCELLED"])
    ).subquery()

    ready_tasks = db.execute(
        select(Task)
        .where(
            and_(
                Task.status.notin_(["Successful", "Failed", ]),
                Task.id.notin_(task_process_check),
            )
        )
    )
    for task in ready_tasks:

    db.commit()
    db.close()
