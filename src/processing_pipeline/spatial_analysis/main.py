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
from src.processing_pipeline.spatial_analysis.create_grid import create_grid
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity
from src.processing_pipeline.spatial_analysis.analyse_grid import analyze_grid_observations
from typing import Dict

report_router = APIRouter()
settings = get_settings()


def get_spatial_analysis(id: str, aoi_polygon: Polygon):
    try:

        query = (
            f'SELECT ST_ASGEOJSON(geo) as valid_area, \n'
            f'ST_ASGEOJSON(ndvi_polygons) as NDVI, \n'
            f'ST_ASGEOJSON(water_hyacinth_classification) as WHC, \n'
            f'utc_capture_start as date, \n'
            f'FROM `{settings.DATABASE_REPORT_TABLE}` \n'
            f'WHERE process_id=\'{id}\' \n'
        )

        client = bigquery.Client.from_service_account_info(
            json.loads(settings.AIPDET_BE_SA_GCP)
        )

        query_job = client.query(query)
        result = query_job.result()

        area_data = []

        for row in result:
            oneRowData = {}

            if row.NDVI:
                ndvi_dict = json.loads(row.NDVI)
                # extract_geometry(ndvi_dict)
                oneRowData["NDVI"] = extract_geometry(ndvi_dict)
            else:
                oneRowData["NDVI"] = None

            if row.WHC:
                whc_dict = json.loads(row.WHC)
                # extract_geometry(ndvi_dict)
                oneRowData["WHC"] = extract_geometry(whc_dict)
            else:
                oneRowData["WHC"] = None

            valid_area_dict = json.loads(row.valid_area)
            oneRowData["valid_area"] = extract_geometry(valid_area_dict)
            area_data.append(oneRowData)

    except Exception as e:
        print(e)

    ndvi_areas = [data['NDVI'] for data in area_data]
    whc_areas = [data['WHC'] for data in area_data]
    observed_areas = [data['valid_area'] for data in area_data]

    grid_gdf = create_grid(aoi_polygon, cell_size=100)
    analyzed_grid = analyze_grid_observations(
        grid_gdf, observed_areas, ndvi_areas, whc_areas)
    grid_gdf['process_id'] = id

    upload_grid_to_bigquery(grid_gdf)
    return analyzed_grid.to_json()


def extract_geometry(geom_dict: Dict) -> Polygon | MultiPolygon:

    if geom_dict['type'] == 'MultiPolygon':

        polygons = []
        for coords_array in geom_dict['coordinates']:
            for polygon_coords in coords_array:
                polygon = Polygon(polygon_coords)
                if not polygon.is_valid:
                    polygon = polygon.buffer(0)

                polygons.append(polygon)
        return MultiPolygon(polygons)

    elif geom_dict['type'] == 'Polygon':
        outer_ring = geom_dict['coordinates'][0]

        if len(geom_dict['coordinates']) > 1:
            holes = geom_dict['coordinates'][1:]

        else:
            holes = None
        polygon = Polygon(outer_ring, holes)
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        return polygon
    else:
        raise ValueError(
            "Invalid GeoJSON type for NDVI area. Must be 'Polygon' or 'Multipolygon'")

    # Extract geometry from GeoJSON


def upload_grid_to_bigquery(grid_gdf):
    client = bigquery.Client.from_service_account_info(
        json.loads(settings.AIPDET_BE_SA_GCP)
    )
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("process_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("cell_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("cell_area", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("total_observed_area",
                                 "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("cell_intersection_area",
                                 "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("cell_coverage_ratio",
                                 "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("total_ndvi_area", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("ndvi_score", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("geometry", "GEOGRAPHY", mode="REQUIRED"),
            bigquery.SchemaField("whc_score", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("total_whc_area", "FLOAT", mode="REQUIRED"),
        ],
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_dataframe(
        grid_gdf,
        settings.DATABASE_GRID_TABLE,
        job_config=job_config
    )

    job.result()
    client.close()
    print(
        f"Grid data uploaded to BigQuery table {settings.DATABASE_REPORT_TABLE}")
