import numpy as np
from shapely.geometry import Polygon, MultiPolygon
import geopandas as gpd  # type: ignore
from src.processing_pipeline.spatial_analysis.utils import get_utm_zone_from_WGS84
from typing import List


def analyze_grid_observations(
    grid_gdf: gpd.GeoDataFrame,
    observed_areas: List[Polygon | MultiPolygon],
    ndvi_areas: List[Polygon | MultiPolygon],
    whc_areas: List[Polygon | MultiPolygon]
) -> gpd.GeoDataFrame:
    grid_center = grid_gdf.unary_union.centroid
    target_utm = get_utm_zone_from_WGS84(grid_center.x, grid_center.y)
    grid_gdf_utm = grid_gdf.to_crs(f"EPSG:{target_utm}")

    grid_gdf_utm['total_observed_area'] = 0.0
    grid_gdf_utm['total_ndvi_area'] = 0.0
    grid_gdf_utm['total_whc_area'] = 0.0

    def process_geometry(geom):
        if isinstance(geom, MultiPolygon):
            return [poly for poly in geom.geoms]
        return [geom]

    for obs_geom in observed_areas:
        for poly in process_geometry(obs_geom):
            if not poly.is_valid:
                poly = poly.buffer(0)
            obs_utm = gpd.GeoDataFrame(
                geometry=[poly], crs="EPSG:4326").to_crs(grid_gdf_utm.crs)
            grid_gdf_utm['total_observed_area'] += grid_gdf_utm.geometry.intersection(
                obs_utm.geometry.iloc[0]).area

    for ndvi_geom in ndvi_areas:
        for poly in process_geometry(ndvi_geom):
            if not poly.is_valid:
                poly = poly.buffer(0)
            ndvi_utm = gpd.GeoDataFrame(
                geometry=[poly], crs="EPSG:4326").to_crs(grid_gdf_utm.crs)
            grid_gdf_utm['total_ndvi_area'] += grid_gdf_utm.geometry.intersection(
                ndvi_utm.geometry.iloc[0]).area

    for whc_geom in whc_areas:
        for poly in process_geometry(whc_geom):
            if not poly.is_valid:
                poly = poly.buffer(0)
            whc_utm = gpd.GeoDataFrame(
                geometry=[poly], crs="EPSG:4326").to_crs(grid_gdf_utm.crs)
            grid_gdf_utm['total_whc_area'] += grid_gdf_utm.geometry.intersection(
                whc_utm.geometry.iloc[0]).area

    grid_gdf_utm['ndvi_score'] = np.where(
        grid_gdf_utm['total_observed_area'] > 0,
        grid_gdf_utm['total_ndvi_area'] / grid_gdf_utm['total_observed_area'],
        0
    )
    grid_gdf_utm['whc_score'] = np.where(
        grid_gdf_utm['total_observed_area'] > 0,
        grid_gdf_utm['total_whc_area'] / grid_gdf_utm['total_observed_area'],
        0
    )

    return grid_gdf_utm.to_crs("EPSG:4326").fillna(0)
