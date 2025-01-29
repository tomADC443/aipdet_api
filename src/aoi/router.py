from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.database import get_db
from src.aoi.models import AOI
from src.aoi.schemas import AOICreationRequest, AoiGetResponse, AOIDeletionRequest, aoi_id_parameter
from fastapi.responses import JSONResponse
from src.dependencies import get_current_user, login_required

aoi_router = APIRouter()
aois_router = APIRouter()


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
@ aois_router.get("", response_model=AoiGetResponse)
def get_aois(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    aoi_query = select(AOI).where(AOI.user_id == user_id)
    aoi_query_result = db.execute(aoi_query).scalars().all()
    responseData = [
        {
            "id": str(aoi.id),
            "name": aoi.name,
            "description": aoi.description,
            "geometry": aoi.geometry,
            "createdAt": int(aoi.created_at.timestamp()),

        } for aoi in aoi_query_result
    ]
    return {"aois": responseData}


@ login_required
@ aoi_router.delete("")
def delete_aois(data: AOIDeletionRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):

    user_id = current_user['sub']
    aoi_id = data.id
    """
    Delete an AOI for a specific user.
    Validates ownership and handles the deletion process.
    """
    try:
        result = db.execute(
            select(AOI)
            .where(AOI.id == aoi_id)
            .where(AOI.user_id == user_id)
        ).scalars().first()
        print(result)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AOI not found or you don't have permission to delete it."
            )

        # Delete the AOI
        db.delete(result)
        print("is gelöscht")
        db.commit()
        print("is commited")
        return {
            "message": "AOI successfully deleted.",
            "id": aoi_id
        }

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ login_required
@ aoi_router.get("")
def get_aoi(
        id: str = aoi_id_parameter,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)):

    user_id = current_user['sub']
    aoi_query = select(AOI).where(AOI.user_id == user_id).where(AOI.id == id)
    aoi = db.execute(aoi_query).scalars().first()
    if not aoi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AOI not found."
        )
    responseData = {
        "id": str(aoi.id),
        "name": aoi.name,
        "description": aoi.description,
        "geometry": aoi.geometry,
        "createdAt": int(aoi.created_at.timestamp()),
    }

    return {"aoi": responseData}
