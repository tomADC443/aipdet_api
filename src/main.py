from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from src.database import Base, engine, get_db, close_connector
from src.user.router import user_router
from google.cloud import bigquery
from fastapi.responses import JSONResponse
from src.dependencies import get_current_user, login_required
from src.aoi.router import aoi_router
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
),

# Include user router
app.include_router(user_router, prefix="/api/user",
                   tags=["User and Authentication"])
app.include_router(aoi_router, prefix="/api/aoi",
                   tags=["AOI - Area of Interest"])

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


@app.get("/api/db")
def read_root(db: Session = Depends(get_db)):
    # Example query to verify the database connection
    result = db.execute("SELECT 1").fetchall()
    return {"result": result}


@app.get("/test/db")
async def run_query():
    query = """
    SELECT * FROM `aiap-436610.comp_gee_data.process`
    LIMIT 10
    """
    try:
        # Initialize BigQuery client
        client = bigquery.Client.from_service_account_json(
            'private-key-bigQuery-account.json')
        query_job = client.query(query)  # Make API request
        results = query_job.result()  # Wait for job to complete

        # Convert the results to a list of dictionaries
        print(results)
        return [dict(row) for row in results]
    except Exception as e:
        return {"error": str(e)}
