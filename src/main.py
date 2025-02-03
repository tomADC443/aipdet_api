from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.database import Base, engine
from src.user.router import user_router
from fastapi.responses import JSONResponse
from src.aoi.router import aoi_router
from src.aoi.router import aois_router
from src.task.router import task_router
from src.task.router import tasks_router
from src.report.router import report_router
from src.processing_pipeline.scheduler.scheduler import start_scheduler, shutdown_scheduler
from src.config import get_settings
# Creates app instance
app = FastAPI()


# Register pipeline scheduler
@app.on_event("shutdown")
def shutdown_event():
    shutdown_scheduler()


@app.on_event("startup")
def startup_event():
    start_scheduler()


# CORS configuration
settings = get_settings()

origins = ["http://localhost:5173"] if settings.RUNNING_ENV == "development" else [
    "aipdet.com",
    "www.aipdet.com",
    "https://aipdet.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["OPTIONS", "GET", "POST", "DELETE"],
    allow_headers=["*"]
)

# Include user router
app.include_router(user_router, prefix="/api/user",
                   tags=["User and Authentication"])
app.include_router(aoi_router, prefix="/api/aoi",
                   tags=["AOI - Area of Interest"])
app.include_router(aois_router, prefix="/api/aois",
                   tags=["AOI - Area of Interest"])
app.include_router(task_router, prefix="/api/task",
                   tags=["Task"])
app.include_router(tasks_router, prefix="/api/tasks",
                   tags=["Task"])
app.include_router(report_router, prefix="/api/report",
                   tags=["Report"])

# Initialize database models
Base.metadata.create_all(bind=engine)


@ app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled error: {exc}")

    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
        # Add CORS headers
        headers={"Access-Control-Allow-Origin": origins},
    )
