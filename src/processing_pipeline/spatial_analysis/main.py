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
from src.report.service import create_grid
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity
from src.report.service import analyze_grid_observations
from typing import Dict

report_router = APIRouter()
settings = get_settings()


def get_spatial_analysis():
    try:
        id = 'bbee7eca-4485-42b5-bbd0-02a8d14bb864'

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
        print(result.max_results)
        print(result.total_rows)

        area_data = []

        for row in result:
            # print(row.valid_area[:100])
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
        print(row.NDVI)
        print(e)

    print("before grid")
    ndvi_areas = [data['NDVI'] for data in area_data]
    whc_areas = [data['WHC'] for data in area_data]
    observed_areas = [data['valid_area'] for data in area_data]

    aoi = json.loads("{\"type\": \"Feature\", \"geometry\": {\"type\": \"Polygon\", \"coordinates\":  [          [            [              27.8515051478241,              -25.728252637136166            ],            [              27.85019542055346,              -25.729907741983737            ],            [              27.850595614998042,              -25.730546835709433            ],            [              27.85070475893633,              -25.730792640073474            ],            [              27.851159525350738,              -25.730907348602557            ],            [              27.8524328713072,              -25.732005267498963            ],            [              27.854160983678128,              -25.733037629749617            ],            [              27.854979563222997,              -25.734659895170907            ],            [              27.854979563222997,              -25.735970800550263            ],            [              27.85548890160584,              -25.73757663993672            ],            [              27.854379271557548,              -25.740460541913663            ],            [              27.852560205903984,              -25.741099578902734            ],            [              27.84790280655244,              -25.743508767858785            ],            [              27.88413060101982,              -25.73945085598133            ],            [              27.88340305006969,              -25.738498346884896            ],            [              27.882972271037517,              -25.737833134491865            ],            [              27.883033810898723,              -25.737403516175547            ],            [              27.88229533255813,              -25.737666830811023            ],            [              27.881141460150047,              -25.738027155157297            ],            [              27.878541400991338,              -25.737625254855487            ],            [              27.8768182848616,              -25.737126342243343            ],            [              27.872510494539057,              -25.734756478741772            ],            [              27.867895004906813,              -25.734964363395548            ],            [              27.86594443786086,              -25.73369600241469            ],            [              27.866605991375593,              -25.73276743823783            ],            [              27.863836697596696,              -25.73109046067536            ],            [              27.859221207964453,              -25.73084099091757            ],            [              27.857855844600664,              -25.730400859914695            ],            [              27.85788636436058,              -25.730125923315057            ],            [              27.85721492963677,              -25.72971351722356            ],            [              27.8570623308361,              -25.729493566722766            ],            [              27.8558720601892,              -25.729576048208457            ],            [              27.855170105705554,              -25.729246121923197            ],            [              27.854010354819735,              -25.729273615815032            ],            [              27.852728524891972,              -25.72902617055773            ],            [              27.852270728489884,              -25.72850378443478            ],            [              27.8515051478241,              -25.728252637136166            ]          ]        ]}, \"properties\": {}}")  # GeoJSONPolygonFeature.validate(aoi)
    aoi_polygon = Polygon(aoi['geometry']['coordinates'][0])

    grid_gdf = create_grid(aoi_polygon, cell_size=100)
    print("after grid")
    analyzed_grid = analyze_grid_observations(
        grid_gdf, observed_areas, ndvi_areas, whc_areas)
    print("after analysis")
    grid_gdf['process_id'] = 'someProcessId_1'

    upload_grid_to_bigquery(grid_gdf)
    print("after upload")
    return analyzed_grid.to_json()


def extract_geometry(geom_dict: Dict) -> Polygon | MultiPolygon:

    if geom_dict['type'] == 'MultiPolygon':

        polygons = []
        for coords_array in geom_dict['coordinates']:
            for polygon_coords in coords_array:
                polygon = Polygon(polygon_coords)
                if not polygon.is_valid:
                    print("Why invalid:", explain_validity(polygon))
                    polygon = polygon.buffer(0)

                polygons.append(polygon)
        return MultiPolygon(polygons)

    elif geom_dict['type'] == 'Polygon':
        outer_ring = geom_dict['coordinates'][0]

        if len(geom_dict['coordinates']) > 1:
            print("Holes detected!!")
            holes = geom_dict['coordinates'][1:]

        else:
            holes = None
        polygon = Polygon(outer_ring, holes)
        if not polygon.is_valid:
            print("Why invalid:", explain_validity(polygon))
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
