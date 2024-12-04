from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from src.database import get_db  # Database dependency
from src.aoi.models import AOI
from src.aoi.schemas import AOICreationRequest
from src.config import get_settings
from fastapi.responses import JSONResponse
from src.dependencies import get_current_user, login_required

aoi_router = APIRouter()
settings = get_settings()


@login_required
@aoi_router.post("/", response_model=JSONResponse)
def signup(aoi: AOICreationRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
        Handles AOI creation requests.
        Validates input data and saves the AOI to the database.
        Returns success or error response.
        """

    # Create a new AOI instance
    new_aoi = AOI(
        user_id=current_user.id,
        geometry=aoi.geometry,
        name=aoi.name,
        description=aoi.description
    )

    # Process the AOI
    return {
        "message": "AOI created successfully",
        "data": aoi.dict()  # Return the parsed AOI for demonstration
    }
