from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from fastapi import FastAPI
import logging
from datetime import datetime

app = FastAPI()
scheduler = BackgroundScheduler()
logger = logging.getLogger(__name__)


def example_task():
    logger.info(f"Starting task at {datetime.now()}")
    # Your function call here
    logger.info(f"Finished task at {datetime.now()}")


@app.on_event("startup")
def start_scheduler():

    scheduler.add_job(
        example_task,
        trigger='cron',
        minute='*/59',
        id="periodic_task",
    )
    scheduler.start()


@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()
