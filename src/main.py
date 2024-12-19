from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from src.database import Base, engine, close_connector
from src.user.router import user_router
from fastapi.responses import JSONResponse
from src.dependencies import get_current_user, login_required
from src.aoi.router import aoi_router
from src.task.router import task_router
from src.gee.task_processing.main import start_task_process
from src.gee.task_processing.metadata import GeeTaskProcessingMetadata
from shapely.geometry import Polygon
from src.gee.schemas import GeoJSONPolygonFeature
import json
# Creates app instance
app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:5173",
    "localhost:5173",
    "http://127.0.0.1:61235",
    " 127.0.0.1:52701",
    "127.0.0.1:61179",
    "127.0.0.1:61235",
    "127.0.0.1:60496",
    "127.0.0.1:60529"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specify frontend origin
    allow_credentials=True,  # Allow cookies and credentials if needed
    # Allow all methods (GET, POST, etc.)
    allow_methods=["OPTIONS", "GET", "POST"],
    allow_headers=["*"],  # Allow all headers
)

# Include user router
app.include_router(user_router, prefix="/api/user",
                   tags=["User and Authentication"])
app.include_router(aoi_router, prefix="/api/aoi",
                   tags=["AOI - Area of Interest"])
app.include_router(task_router, prefix="/api/task",
                   tags=["Task"])

# Initialize database models
Base.metadata.create_all(bind=engine)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the error (optional)
    print(f"Unhandled error: {exc}")

    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
        # Add CORS headers
        headers={"Access-Control-Allow-Origin": "http://localhost:5173"},
    )


@app.get("/protected-endpoint")
@login_required
def some(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello, {current_user['email']}!"}


@app.get("/api/public")
def public():
    """No access token required to access this route"""
    return {
        "status": "success",
        "msg": "Hello from a public endpoint! You don't need to be authenticated to see this."
    }


@app.on_event("shutdown")
def shutdown_event():
    # Close the connector when the application shuts down
    close_connector()


@app.get("/test/gee")
def run_gee_task():
    aoi = json.loads(
        "{\"type\":\"Feature\",\"properties\":{},\"geometry\":{\"coordinates\":[[[27.85666256350123,-25.73526101250701],[27.856568105989453,-25.737749836944474],[27.860682574849562,-25.737826769838705],[27.860671019950587,-25.735313853089494],[27.85666256350123,-25.73526101250701]]],\"type\":\"Polygon\"}}"
    )
    # GeoJSONPolygonFeature.validate(aoi)
    aoi = Polygon(aoi['geometry']['coordinates'][0])

    metadata = GeeTaskProcessingMetadata(
        process_id="1", user_id="1", aoi_id="1")

    start_task_process(aoi, metadata)
