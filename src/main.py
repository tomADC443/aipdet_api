from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from src.database import Base, engine, close_connector
from src.user.router import user_router
from fastapi.responses import JSONResponse
from src.dependencies import get_current_user, login_required
from src.aoi.router import aoi_router
from src.task.router import task_router
from src.gee.task_processing._00_main import start_task_process
from src.gee.task_processing.metadata import GeeTaskProcessingMetadata
from shapely.geometry import Polygon

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


@app.get("/test/gee/mueritz")
def run_gee_task():

    aoi = json.loads("{\"type\": \"Feature\", \"geometry\": {\"type\": \"Polygon\", \"coordinates\": [          [            [              12.653030991582966,              53.50993122436756            ],            [              12.655318271021002,              53.5046160073677            ],            [              12.686662470716868,              53.50355792254416            ],            [              12.685476473971221,              53.510535756594464            ],            [              12.666119312808007,              53.516051714819724            ],            [              12.653030991582966,              53.50993122436756            ]          ]        ]}, \"properties\": {}}")
    # GeoJSONPolygonFeature.validate(aoi)
    aoi = Polygon(aoi['geometry']['coordinates'][0])

    metadata = GeeTaskProcessingMetadata(
        process_id="1", user_id="1", aoi_id="1")

    start_task_process(aoi, metadata)


@app.get("/test/gee/hartbeespoortDammClassic")
def run_gee_taskA():

    aoi = json.loads("{\"type\": \"Feature\", \"geometry\": {\"type\": \"Polygon\", \"coordinates\":  [          [            [              27.87801310266525,              -25.756383849103443            ],            [              27.876398131224988,              -25.742703275558796            ],            [              27.858427819319417,              -25.73498202767223            ],            [              27.866008190311447,              -25.75763503433197            ],            [              27.87801310266525,              -25.756383849103443            ]          ]        ]}, \"properties\": {}}")
    # GeoJSONPolygonFeature.validate(aoi)
    aoi = Polygon(aoi['geometry']['coordinates'][0])

    metadata = GeeTaskProcessingMetadata(
        process_id="2", user_id="1", aoi_id="1")

    start_task_process(aoi, metadata)


@app.get("/test/gee/hartbeespoortDammNewComplex")
def run_gee_taskB():

    aoi = json.loads("{\"type\": \"Feature\", \"geometry\": {\"type\": \"Polygon\", \"coordinates\":  [          [            [              27.8515051478241,              -25.728252637136166            ],            [              27.85019542055346,              -25.729907741983737            ],            [              27.850595614998042,              -25.730546835709433            ],            [              27.85070475893633,              -25.730792640073474            ],            [              27.851159525350738,              -25.730907348602557            ],            [              27.8524328713072,              -25.732005267498963            ],            [              27.854160983678128,              -25.733037629749617            ],            [              27.854979563222997,              -25.734659895170907            ],            [              27.854979563222997,              -25.735970800550263            ],            [              27.85548890160584,              -25.73757663993672            ],            [              27.854379271557548,              -25.740460541913663            ],            [              27.852560205903984,              -25.741099578902734            ],            [              27.84790280655244,              -25.743508767858785            ],            [              27.88413060101982,              -25.73945085598133            ],            [              27.88340305006969,              -25.738498346884896            ],            [              27.882972271037517,              -25.737833134491865            ],            [              27.883033810898723,              -25.737403516175547            ],            [              27.88229533255813,              -25.737666830811023            ],            [              27.881141460150047,              -25.738027155157297            ],            [              27.878541400991338,              -25.737625254855487            ],            [              27.8768182848616,              -25.737126342243343            ],            [              27.872510494539057,              -25.734756478741772            ],            [              27.867895004906813,              -25.734964363395548            ],            [              27.86594443786086,              -25.73369600241469            ],            [              27.866605991375593,              -25.73276743823783            ],            [              27.863836697596696,              -25.73109046067536            ],            [              27.859221207964453,              -25.73084099091757            ],            [              27.857855844600664,              -25.730400859914695            ],            [              27.85788636436058,              -25.730125923315057            ],            [              27.85721492963677,              -25.72971351722356            ],            [              27.8570623308361,              -25.729493566722766            ],            [              27.8558720601892,              -25.729576048208457            ],            [              27.855170105705554,              -25.729246121923197            ],            [              27.854010354819735,              -25.729273615815032            ],            [              27.852728524891972,              -25.72902617055773            ],            [              27.852270728489884,              -25.72850378443478            ],            [              27.8515051478241,              -25.728252637136166            ]          ]        ]}, \"properties\": {}}")    # GeoJSONPolygonFeature.validate(aoi)
    aoi = Polygon(aoi['geometry']['coordinates'][0])

    metadata = GeeTaskProcessingMetadata(
        process_id="3", user_id="1", aoi_id="1")

    start_task_process(aoi, metadata)


@app.get("/test/gee/TiticacaLake")
def run_gee_taskC():

    aoi = json.loads("{\"type\": \"Feature\", \"geometry\": {\"type\": \"Polygon\", \"coordinates\":  [          [            [              -69.17763669984312,              -15.99539743909773            ],            [              -69.17891086718613,              -15.9953811079437            ],            [              -69.17984525657076,              -15.995707730762987            ],            [              -69.18105146832237,              -15.995822048622372            ],            [              -69.18157812415727,              -15.999512847263418            ],            [              -69.1792506451445,              -16.00315458618232            ],            [              -69.17826528906544,              -16.00366083162932            ],            [              -69.17653242147894,              -16.005604149008363            ],            [              -69.17378022001802,              -16.008788536315052            ],            [              -69.16659816342785,              -16.00631847320183            ],            [              -69.16869204509483,              -15.996826337800798            ],            [              -69.17254003047108,              -15.997863427975744            ],            [              -69.17473159830105,              -15.996981554654468            ],            [              -69.17714402180358,              -15.996654933916929            ],            [              -69.17763669984312,              -15.99539743909773            ]          ]        ]}, \"properties\": {}}")    # GeoJSONPolygonFeature.validate(aoi)
    aoi = Polygon(aoi['geometry']['coordinates'][0])

    metadata = GeeTaskProcessingMetadata(
        process_id="4", user_id="1", aoi_id="1")

    start_task_process(aoi, metadata)
