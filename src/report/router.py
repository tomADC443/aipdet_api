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
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity
from scipy import signal
from statsmodels.tsa.seasonal import seasonal_decompose
from typing import Dict
import numpy as np
from datetime import datetime, timedelta
import calendar

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


@report_router.get("/season-analysis")
def get_season_analysis(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    # current_user: dict = Depends(get_current_user)
):

    try:
        query = (
            f'SELECT \n'
            f'utc_capture_start as capture_date, \n'
            # f'SUM(ST_AREA(ndvi_polygons)) as NDVI_AREA, \n'
            # f'SUM(ST_AREA(geo)) as OBSERVED_AREA, \n'
            f'ROUND(SUM(ST_AREA(ndvi_polygons))/ SUM(ST_AREA(geo)),4)*100 AS NDVI_SCORE \n'
            f'FROM `{settings.DATABASE_REPORT_TABLE}` \n'
            f'WHERE \n'
            f'process_id = \'{task_id}\' \n'
            f'GROUP BY \n'
            f'capture_date \n'
            f'ORDER BY \n'
            f'capture_date ASC \n'
        )
        print(query)

        client = bigquery.Client.from_service_account_info(
            json.loads(settings.AIPDET_BE_SA_GCP)
        )

        query_job = client.query(query)
        result = query_job.result()

        capture_dates = []
        ndvi_scores = []

        for row in result:
            if row.NDVI_SCORE is None:
                continue
            capture_dates.append(row.capture_date)
            ndvi_scores.append(row.NDVI_SCORE)

        client.close()

        df = pd.DataFrame({
            'capture_date': capture_dates,
            'ndvi_score': ndvi_scores
        })
        df['capture_date'] = pd.to_datetime(df['capture_date'])

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    df = pd.DataFrame({
        'capture_date': capture_dates,
        'ndvi_score': ndvi_scores
    })
    df['capture_date'] = pd.to_datetime(df['capture_date'])

    result = analyze_seasonal_patterns_weekly(df)
    print(result)
    # Test various weeks
    test_weeks = [1, 2, 3, 26, 52, 53]
    for week in test_weeks:
        print(f"Week {week}: {get_week_description(week)}")
    return


def analyze_seasonal_patterns_weekly(df):
    # data preparation
    df['week'] = df['capture_date'].dt.isocalendar().week
    weekly_means = df.groupby('week')['ndvi_score'].mean()

    # smoothing
    smoothed_values = weekly_means.rolling(
        window=2, center=True, min_periods=1).mean()

    # Get above/below threshold
    threshold = smoothed_values.mean()
    above_threshold = smoothed_values > threshold

    # Find blocks
    blocks = []
    start = None

    for week in sorted(above_threshold.index):
        if above_threshold[week]:
            if start is None:
                start = week
        else:
            if start is not None:
                blocks.append([start, week - 1])
                start = None

    # add last block if not ended
    if start is not None:
        blocks.append([start, max(above_threshold.index)])

    # check if blocks are 2 weeks or less apart and merge them
    i = 0
    while i < len(blocks) - 1:
        if blocks[i+1][0] - blocks[i][1] <= 2:
            blocks[i][1] = blocks[i+1][1]
            blocks.pop(i+1)
        else:
            i += 1

    # check if the last block is two weeks or less apart from the first block and merge them
    if len(blocks) >= 2:
        last_week = 53
        if blocks[0][0] <= 2 or (last_week - blocks[-1][1]) <= 2:
            merged = [blocks[-1][0], blocks[0][1]]
            blocks = [merged] + blocks[1:-1]

    # check if all blocks have a minimum length of 6 (otherwise remove them)
    blocks = [block for block in blocks if (block[1] - block[0] + 1) >= 6]

    # Convert blocks to strings for output
    block_descriptions = []
    for block in blocks:
        block_descriptions.append(f"Week {block[0]} to Week {block[1]}")

    return {
        'weekly_means': weekly_means,
        'smoothed_values': smoothed_values,
        'threshold': threshold,
        'blocks': block_descriptions,
        'above_threshold': above_threshold,
        'raw_blocks': blocks
    }


def get_week_description(week_number: int) -> str:
    # Handle special case for week 53
    if week_number == 53:
        # Check if current year has 53 weeks
        current_year = datetime.now().year
        last_day = datetime(current_year, 12, 31)
        if last_day.isocalendar()[1] != 53:
            return "Late December"  # Default for non-existent week 53

    # Get current year
    current_year = datetime.now().year

    # Get the monday of the requested week
    monday = datetime.strptime(
        f'{current_year}-W{week_number:02d}-1', '%Y-W%W-%w')

    # Get the month name
    month = monday.strftime('%B')

    # Calculate which part of the month we're in
    day_of_month = monday.day
    _, last_day = calendar.monthrange(current_year, monday.month)

    if day_of_month <= 10:
        part = "Early"
    elif day_of_month > 21:
        part = "Late"
    else:
        part = "Mid"

    return f"{part} {month}"
