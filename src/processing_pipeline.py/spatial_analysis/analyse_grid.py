from pyproj import Transformer
import numpy as np
from shapely.geometry import box, Polygon, MultiPolygon
from shapely.validation import make_valid
import geopandas as gpd  # type: ignore
from src.report.utils import get_utm_zone_from_WGS84
from typing import List, Optional


def analyze_grid_observations(
    grid_gdf: gpd.GeoDataFrame,
    observed_areas: List[Polygon | MultiPolygon],
    ndvi_areas: List[Optional[Polygon | MultiPolygon]],
    whc_areas: List[Optional[Polygon | MultiPolygon]]
) -> gpd.GeoDataFrame:
    """
    Analyze satellite observations per grid cell using area summation.

    Args:
        grid_gdf: GeoDataFrame containing grid cells
        observed_areas: List of observed area polygons
        ndvi_areas: List of NDVI area polygons (can contain None)

    Returns:
        GeoDataFrame with columns:
        - total_observed_area: Sum of all observed areas in the cell
        - total_ndvi_area: Sum of all NDVI areas in the cell
        - ndvi_score: Ratio of NDVI area to observed area
    """
    if len(observed_areas) != len(ndvi_areas):
        raise ValueError(
            "observed_areas and ndvi_areas must have the same length")

    results = []

    for idx, cell in grid_gdf.iterrows():
        cell_geom = cell.geometry
        total_observed_area = 0
        total_ndvi_area = 0
        total_whc_area = 0

        for obs_area, ndvi_area, whc_area in zip(observed_areas, ndvi_areas, whc_areas):
            # Calculate observed area intersection
            if safe_intersection(cell_geom, obs_area):

                intersection = safe_intersection(cell_geom, obs_area)
                total_observed_area += intersection.area

            # Calculate NDVI area intersection

            if ndvi_area is not None and safe_intersection(cell_geom, ndvi_area):

                ndvi_intersection = safe_intersection(cell_geom, ndvi_area)
                total_ndvi_area += ndvi_intersection.area

            if whc_area is not None and safe_intersection(cell_geom, whc_area):

                whc_intersection = safe_intersection(cell_geom, whc_area)
                total_whc_area += whc_intersection.area

        results.append({
            'total_observed_area': total_observed_area,
            'total_ndvi_area': total_ndvi_area,
            'total_whc_area': total_whc_area,
            # avoiding division by zero
            'ndvi_score': (total_ndvi_area / total_observed_area) if total_observed_area > 0 else 0,
            # avoiding division by zero
            'whc_score': (total_whc_area / total_observed_area) if total_observed_area > 0 else 0
        })

    for col in ['total_observed_area', 'total_ndvi_area', 'total_whc_area', 'ndvi_score', 'whc_score']:
        grid_gdf[col] = [r[col] for r in results]

    return grid_gdf


def safe_intersection(geom1, geom2):
    """Safely perform intersection between two geometries"""
    try:
        # First try normal intersection
        return geom1.intersection(geom2)
    except Exception as e:
        try:
            # If that fails, try with validated geometries
            valid_geom1 = make_valid(geom1)
            valid_geom2 = make_valid(geom2)
            return valid_geom1.intersection(valid_geom2)
        except Exception as e:
            # If all fails, try with buffer(0)
            print(f"WARN: Using buffer(0) to fix geometry: {str(e)}")
            return geom1.buffer(0).intersection(geom2.buffer(0))
