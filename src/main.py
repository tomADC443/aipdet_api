from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from src.database import Base, engine, close_connector
from src.user.router import user_router
from fastapi.responses import JSONResponse
from src.dependencies import get_current_user, login_required
from src.aoi.router import aoi_router
from src.task.router import task_router
from src.gee.task_processing.main import start_task_process
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
    aoi = json.loads("{\"type\":\"Feature\",\"properties\":{},\"geometry\":{\"coordinates\":[[[27.847920511878414,-25.725698453463608],[27.849648903757668,-25.72786102203966],[27.85089541547137,-25.730387610357084],[27.854595997118707,-25.732984325731593],[27.855725648358202,-25.736212595481177],[27.85560878788533,-25.73926533512784],[27.849298322338996,-25.7426337844268],[27.858841927641066,-25.752001781917002],[27.876682626534233,-25.747300332443075],[27.861971869876754,-25.73272592686331],[27.857284896304805,-25.72992186217361],[27.852621021936017,-25.728958737688274],[27.851037692232808,-25.728175513503146],[27.850507559519656,-25.726851025094106],[27.84953918376266,-25.727073896772637],[27.849411951912174,-25.726430751650298],[27.848881819198,-25.72544373999429],[27.84835168648479,-25.725749396092],[27.847920511878414,-25.725698453463608]]],\"type\":\"Polygon\"}}")

    start_task_process(aoi)
