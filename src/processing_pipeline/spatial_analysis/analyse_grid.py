from pyproj import Transformer
import numpy as np
from shapely.geometry import box, Polygon, MultiPolygon
from shapely.validation import make_valid
from shapely.ops import transform
import geopandas as gpd  # type: ignore
from src.report.utils import get_utm_zone_from_WGS84
from typing import List, Optional


def analyze_grid_observations(
    grid_gdf: gpd.GeoDataFrame,
    observed_areas: List[Polygon | MultiPolygon],
    ndvi_areas: List[Polygon | MultiPolygon],
    whc_areas: List[Polygon | MultiPolygon]
) -> gpd.GeoDataFrame:
    """
    Vectorized analysis of satellite observations per grid cell.

    Args:
        grid_gdf: GeoDataFrame containing grid cells
        observed_areas: List of observed area polygons
        ndvi_areas: List of NDVI area polygons (can contain None)
        whc_areas: List of WHC area polygons (can contain None)

    Returns:
        GeoDataFrame with added analysis columns
    """

    # Get target UTM zone and transformer
    grid_center = grid_gdf.unary_union.centroid
    target_utm = get_utm_zone_from_WGS84(grid_center.x, grid_center.y)

    # Create GeoDataFrames from the area lists
    observed_gdf = gpd.GeoDataFrame(
        geometry=[area for area in observed_areas],
        crs="EPSG:4326"
    )
    ndvi_gdf = gpd.GeoDataFrame(
        geometry=[area for area in ndvi_areas],
        crs="EPSG:4326"
    )
    whc_gdf = gpd.GeoDataFrame(
        geometry=[area for area in whc_areas],
        crs="EPSG:4326"
    )

    # Transform all geometries to UTM
    observed_gdf = observed_gdf.to_crs(f"EPSG:{target_utm}")
    ndvi_gdf = ndvi_gdf.to_crs(f"EPSG:{target_utm}")
    whc_gdf = whc_gdf.to_crs(f"EPSG:{target_utm}")
    grid_gdf = grid_gdf.to_crs(f"EPSG:{target_utm}")

    # Perform overlay operations
    observed_overlay = gpd.overlay(grid_gdf, observed_gdf, how='intersection')
    ndvi_overlay = gpd.overlay(grid_gdf, ndvi_gdf, how='intersection')
    whc_overlay = gpd.overlay(grid_gdf, whc_gdf, how='intersection')

    # Calculate areas and group by grid cells
    observed_areas = observed_overlay.groupby(
        level=0)['geometry'].apply(lambda x: x.area.sum())
    ndvi_areas = ndvi_overlay.groupby(
        level=0)['geometry'].apply(lambda x: x.area.sum())
    whc_areas = whc_overlay.groupby(
        level=0)['geometry'].apply(lambda x: x.area.sum())

    # Combine results
    grid_gdf['total_observed_area'] = observed_areas
    grid_gdf['total_ndvi_area'] = ndvi_areas
    grid_gdf['total_whc_area'] = whc_areas

    # Calculate scores
    grid_gdf['ndvi_score'] = np.where(
        grid_gdf['total_observed_area'] > 0,
        grid_gdf['total_ndvi_area'] / grid_gdf['total_observed_area'],
        0
    )
    grid_gdf['whc_score'] = np.where(
        grid_gdf['total_observed_area'] > 0,
        grid_gdf['total_whc_area'] / grid_gdf['total_observed_area'],
        0
    )
    grid_gdf = grid_gdf.to_crs("EPSG:4326")

    # Fill NaN values with 0
    grid_gdf = grid_gdf.fillna(0)

    return grid_gdf
