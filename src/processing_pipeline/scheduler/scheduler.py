from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from fastapi import FastAPI

from datetime import datetime
from src.processing_pipeline.scheduler.pipeline_async_manager import pipeline_organizer
app = FastAPI()
scheduler = BackgroundScheduler()


def start_scheduler():
    pipeline_organizer()
    scheduler.add_job(
        pipeline_organizer,
        trigger='cron',
        minute='*/10',
        id="periodic_task",
    )
    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown()
