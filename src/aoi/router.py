from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.database import get_db  # Database dependency
from src.aoi.models import AOI
from src.aoi.schemas import AOICreationRequest
from src.config import get_settings
from fastapi.responses import JSONResponse
from src.dependencies import get_current_user, login_required

aoi_router = APIRouter()
settings = get_settings()


@login_required
@aoi_router.post("")
def create_aoi(aoi: AOICreationRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
        Handles AOI creation requests.
        Validates input data and saves the AOI to the database.
        Returns success or error response.
        """
    try:
        # Serialize the geometry field
        geometry_as_dict = aoi.geometry.dict() if hasattr(
            aoi.geometry, "dict") else aoi.geometry

        # Create a new AOI instance
        new_aoi = AOI(
            user_id=current_user['sub'],
            geometry=geometry_as_dict,
            name=aoi.name,
            description=aoi.description
        )

        db.add(new_aoi)
        db.commit()
    except Exception as e:
        print(f"Error creating AOI: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."},
        )
    # Process the AOI
    return {"message": "AOI created successfully", }


@ login_required
@ aoi_router.get("")
def get_aois(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    aoi_query_result = select(AOI).where(user_id == user_id)
    print(aoi_query_result)
