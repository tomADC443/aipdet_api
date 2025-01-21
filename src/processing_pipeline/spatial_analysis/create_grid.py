from pyproj import Transformer
import numpy as np
from shapely.geometry import box, Polygon, MultiPolygon
from shapely.validation import make_valid
import geopandas as gpd  # type: ignore
from src.report.utils import get_utm_zone_from_WGS84
from typing import List, Optional


def create_grid(aoi_polygon: Polygon, cell_size: float, source_crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """
    Create a grid over the area of interest in metric coordinates

    Args:
        aoi_polygon: Shapely polygon in source_crs (EPSG:4326)
        cell_size: Size of each grid cell in meters
        source_crs: CRS of input polygon (default: EPSG:4326)

    Returns:
        GeoDataFrame containing the grid cells that intersect with the AOI,
        with their geometries back in EPSG:4326
    """
    # Define utm zone from centroid of aoi_polygon
    lon, lat = aoi_polygon.centroid.x, aoi_polygon.centroid.y
    target_utm = get_utm_zone_from_WGS84(lon, lat)

    # Coordinate Reference System (CRS) Transformers for both Directions
    to_utm = Transformer.from_crs(
        source_crs,
        f"EPSG:{target_utm}",
        always_xy=True
    )
    from_utm = Transformer.from_crs(
        f"EPSG:{target_utm}",
        source_crs,
        always_xy=True
    )

    # Transform polygon to metric CRS (the local UTM)
    projected_coords = [to_utm.transform(x, y)
                        for x, y in aoi_polygon.exterior.coords]
    projected_polygon = Polygon(projected_coords)

    # Create grid in metric coordinates
    minx, miny, maxx, maxy = projected_polygon.bounds

    # Calculate number of cells in each direction
    nx = int(np.ceil((maxx - minx) / cell_size))
    ny = int(np.ceil((maxy - miny) / cell_size))

    # Create grid cells
    grid_cells = []
    cell_ids = []

    for i in range(nx):
        for j in range(ny):
            x0 = minx + i * cell_size
            y0 = miny + j * cell_size
            cell = box(x0, y0, x0 + cell_size, y0 + cell_size)

            if cell.intersects(projected_polygon):
                # Transform cell coordinates back to WGS84
                cell_coords = [(from_utm.transform(x, y))
                               for x, y in cell.exterior.coords]
                grid_cells.append(Polygon(cell_coords))
                cell_ids.append(f"cell_{i}_{j}")

    # Create GeoDataFrame
    grid_gdf = gpd.GeoDataFrame(
        {'cell_id': cell_ids, 'geometry': grid_cells},
        crs=source_crs
    )

    # For area calculations, we need a UTM version of the grid
    grid_gdf_utm = gpd.GeoDataFrame(
        {'cell_id': cell_ids, 'geometry': [box(minx + i * cell_size,
                                               miny + j * cell_size,
                                               minx + (i + 1) * cell_size,
                                               miny + (j + 1) * cell_size)
                                           for i, j in [(int(cid.split('_')[1]),
                                                        int(cid.split('_')[2]))
                                                        for cid in cell_ids]]},
        crs=f"EPSG:{target_utm}"
    )

    # Calculate intersection information in UTM for accurate areas
    grid_gdf['cell_intersection_area'] = grid_gdf_utm.intersection(
        projected_polygon).area
    grid_gdf['cell_area'] = grid_gdf_utm.area
    # avoid division by zero
    grid_gdf['cell_coverage_ratio'] = np.where(
        grid_gdf['cell_area'] > 0,
        grid_gdf['cell_intersection_area'] / grid_gdf['cell_area'],
        0
    )
    grid_gdf = grid_gdf[grid_gdf['cell_intersection_area'] >= 1000]
    return grid_gdf

# Example usage:
# aoi_polygon = Polygon([(lon1, lat1), (lon2, lat2), ...])  # in WGS84
# grid_gdf = create_grid(aoi_polygon, cell_size=100)
