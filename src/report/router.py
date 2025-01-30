from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.config import get_settings
from src.report.schemas import task_id_parameter, dateString
from src.dependencies import get_current_user, login_required
import json
import pandas as pd
from src.report.utils import execute_safe_query, check_task_ownership
from src.report.service import get_monthly_average_pivot, analyze_growth_rate, analyze_seasonal_patterns_weekly

report_router = APIRouter()
settings = get_settings()


@login_required
@report_router.get("/number-total-distinct-images")
def get_distinct_images_count(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_task_ownership(task_id, current_user['sub'])

    query = """
        SELECT COUNT(DISTINCT image_id)
        FROM `{table}`
        WHERE process_id = @task_id
    """.format(table=settings.DATABASE_REPORT_TABLE)

    try:
        result = execute_safe_query(
            query=query,
            params={"task_id": task_id}
        )
        row = next(result, None)

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
@report_router.get("/temporal-range")
def get_temporal_range(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_task_ownership(task_id, current_user['sub'])
    query = """
       SELECT
       MIN(utc_capture_start) as from_date,
       MAX(utc_capture_start) as to_date
       FROM `{table}`
       WHERE process_id = @task_id
   """.format(table=settings.DATABASE_REPORT_TABLE)

    try:
        result = execute_safe_query(
            query=query,
            params={"task_id": task_id}
        )
        row = next(result, None)
        if not row.from_date or not row.to_date:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )
        return {
            "fromDate": row.from_date,
            "toDate": row.to_date
        }
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@login_required
@report_router.get("/total-observed-area")
def get_total_observed_area(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_task_ownership(task_id, current_user['sub'])
    query = """
       SELECT
       ROUND(SUM(ST_AREA(geo)/1000000),0) as area
       FROM `{table}`
       WHERE process_id = @task_id
   """.format(table=settings.DATABASE_REPORT_TABLE)

    try:
        result = execute_safe_query(
            query=query,
            params={"task_id": task_id}
        )
        row = next(result, None)
        if not row.area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )
        return {"area": row.area}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@login_required
@report_router.get("/spatial-analysis")
def get_spatial_analysis(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)

):
    check_task_ownership(task_id, current_user['sub'])
    query = """
       SELECT
       process_id,
       cell_id,
       ROUND(cell_area, 0) as cell_area,
       ROUND(cell_intersection_area, 0) as cell_intersection_area,
       ROUND(cell_coverage_ratio, 2) as cell_coverage_ratio,
       ST_ASGEOJSON(geometry) as geometry,
       ROUND(total_observed_area, 0) as total_observed_area,
       ROUND(total_ndvi_area, 0) as total_ndvi_area,
       ROUND(ndvi_score, 2) as ndvi_score,
       ROUND(total_whc_area, 0) as total_whc_area,
       ROUND(whc_score, 2) as whc_score
       FROM `{table}`
       WHERE process_id = @task_id
   """.format(table=settings.DATABASE_GRID_TABLE)

    try:
        result = execute_safe_query(
            query=query,
            params={"task_id": task_id}
        )

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

        return {
            'type': 'FeatureCollection',
            'features': features
        }
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@login_required
@report_router.get("/season-analysis")
def get_season_analysis(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_task_ownership(task_id, current_user['sub'])
    query = """
       SELECT
       utc_capture_start as capture_date,
       ROUND(SUM(ST_AREA(ndvi_polygons))/ SUM(ST_AREA(geo)),4)*100 AS NDVI_SCORE
       FROM `{table}`
       WHERE process_id = @task_id
       GROUP BY capture_date
       ORDER BY capture_date ASC
   """.format(table=settings.DATABASE_REPORT_TABLE)

    try:

        result = execute_safe_query(
            query=query,
            params={"task_id": task_id}
        )

        capture_dates = []
        ndvi_scores = []

        for row in result:
            if row.NDVI_SCORE is None:
                continue
            capture_dates.append(row.capture_date)
            ndvi_scores.append(row.NDVI_SCORE)

        df = pd.DataFrame({
            'capture_date': capture_dates,
            'ndvi_score': ndvi_scores
        })
        df['capture_date'] = pd.to_datetime(df['capture_date'])

        seasons = analyze_seasonal_patterns_weekly(df)
        monthly_average = get_monthly_average_pivot(df)
        growth_rates = analyze_growth_rate(df)

        return {
            'seasons': seasons,
            'monthly_average': monthly_average,
            'growthRates': growth_rates
        }
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@login_required
@report_router.get("/available-dates")
def get_available_dates(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_task_ownership(task_id, current_user['sub'])

    query = """
       SELECT DISTINCT utc_capture_start as date
       FROM `{table}`
       WHERE process_id = @task_id
   """.format(table=settings.DATABASE_REPORT_TABLE)

    try:
        result = execute_safe_query(
            query=query,
            params={"task_id": task_id}
        )

        dates = [row.date for row in result]
        return sorted(dates, reverse=True)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@login_required
@report_router.get("/analysis-record")
def get_analysis_record(
    task_id: str = task_id_parameter,
    dateString: str = dateString,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_task_ownership(task_id, current_user['sub'])
    query = """
       SELECT 
       ST_ASGEOJSON(geo) as observed_area,
       ST_ASGEOJSON(ndvi_polygons) as ndvi_area,
       ST_ASGEOJSON(water_hyacinth_classification) as whc_area
       FROM `{table}`
       WHERE process_id = @task_id
       AND utc_capture_start = @date_string
   """.format(table=settings.DATABASE_REPORT_TABLE)

    try:
        result = execute_safe_query(
            query=query,
            params={
                "task_id": task_id,
                "date_string": dateString
            }
        )

        record = {
            'observed_areas': [],
            'ndvi_areas': [],
            'whc_areas': [],
            'dateString': dateString
        }

        for row in result:
            if row.observed_area:
                record['observed_areas'].append(json.loads(row.observed_area))
            if row.ndvi_area:
                record['ndvi_areas'].append(json.loads(row.ndvi_area))
            if row.whc_area:
                record['whc_areas'].append(json.loads(row.whc_area))

        return record
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
