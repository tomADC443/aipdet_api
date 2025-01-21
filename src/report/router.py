from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.config import get_settings
from google.cloud import bigquery
from src.report.schemas import task_id_parameter
from src.dependencies import get_current_user, login_required
from sqlalchemy import select, or_
from src.task.models import Task
import json
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity

from typing import Dict

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
        client = bigquery.Client.from_service_account_info(
            json.loads(settings.AIPDET_BE_SA_GCP)
        )
        query_job = client.query(query)
        result = query_job.result()
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
        client = bigquery.Client.from_service_account_info(
            json.loads(settings.AIPDET_BE_SA_GCP)
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


@report_router.get("/spatial-analysis")
def get_spatial_analysis(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)
):

    try:
        query = (
            f'SELECT \n'
            f'process_id, \n'
            f'cell_id, \n'
            f'ROUND(cell_area, 0) as cell_area, \n'
            f'ROUND(cell_intersection_area, 0) as cell_intersection_area, \n'
            f'ROUND(cell_coverage_ratio, 2) as cell_coverage_ratio, \n'
            f'ST_ASGEOJSON(geometry) as geometry, \n'
            f'ROUND(total_observed_area, 0) as total_observed_area, \n'
            f'ROUND(total_ndvi_area, 0) as total_ndvi_area, \n'
            f'ROUND(ndvi_score, 2) as ndvi_score, \n'
            f'ROUND(total_whc_area, 0) as total_whc_area, \n'
            f'ROUND(whc_score, 2) as whc_score \n'
            f'FROM `{settings.DATABASE_GRID_TABLE}` \n'
            f'WHERE process_id =\'{task_id}\' \n'
        )

        client = bigquery.Client.from_service_account_info(
            json.loads(settings.AIPDET_BE_SA_GCP)
        )

        query_job = client.query(query)
        result = query_job.result()

        features = []

        for row in result:
            geometry = json.loads(row.geometry)
            properties = {
                'process_id': row.process_id,
                'cell_id': row.cell_id,
                'cell_area': row.cell_area,
                'cell_intersection_area': row.cell_intersection_area,
                'cell_coverage_ratio': row.cell_coverage_ratio,
                'total_observed_area': row.total_observed_area,
                'total_ndvi_area': row.total_ndvi_area,
                'ndvi_score': row.ndvi_score,
                'total_whc_area': row.total_whc_area,
                'whc_score': row.whc_score
            }

            feature = {
                'type': 'Feature',
                'geometry': geometry,
                'properties': properties
            }
            features.append(feature)

        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        return geojson

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
