from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from fastapi import FastAPI

from datetime import datetime
from src.processing_pipeline.scheduler.pipeline_async_manager import pipeline_organizer
app = FastAPI()
scheduler = BackgroundScheduler()


def example_task():

    print("HULULULULULULLULULULULULULULLULULUL")
    # Your function call here


@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(
        example_task,
        trigger='cron',
        minute='*/45',
        id="periodic_task",
    )
    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown()
