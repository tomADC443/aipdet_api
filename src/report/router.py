

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.config import get_settings
from google.cloud import bigquery
from src.report.schemas import task_id_parameter
from src.dependencies import get_current_user, login_required
from sqlalchemy import select, or_
from src.task.models import Task

report_router = APIRouter()
settings = get_settings()


@login_required
@report_router.get("/number-total-distinct-images")
def get_distinct_images_count(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = (
        f'SELECT COUNT(DISTINCT image_id)\n'
        f'FROM `{settings.DATABASE_REPORT_TABLE}` \n'
        f'WHERE process_id = \'{task_id}\''
    )

    try:
        client = bigquery.Client.from_service_account_json(
            'private-key-bigQuery-account.json'
        )
        query_job = client.query(query)
        result = query_job.result()
        print(result)
        row = next(result, None)
        print(row)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )

        return {"count": row[0]}

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@login_required
@report_router.get("/ndvi-area-data")
def get_ndvi_area_data(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user['sub']
    query = (
        f'SELECT utc_capture_start as date, \n'
        f'SUM(ST_AREA(ndvi_polygons)) as total_area \n'
        f'FROM `{settings.DATABASE_REPORT_TABLE}` \n'
        f'WHERE ndvi_polygons IS NOT NULL \n'
        f'AND process_id=\'{task_id}\' \n'
        f'GROUP BY utc_capture_start \n'
        f'ORDER BY utc_capture_start \n'
    )

    task = db.execute(
        select(Task).where(Task.id == task_id).filter(or_(Task.user_id == user_id, Task.is_public == True))).scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )

    try:
        client = bigquery.Client.from_service_account_json(
            'private-key-bigQuery-account.json'
        )
        query_job = client.query(query)
        result = query_job.result()

        data = [
            {
                "date": row.date.strftime("%Y-%m-%d"),  # Format date as string
                "value": float(row.total_area)  # Ensure value is float
            }

            for row in result
        ]

        return data

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
