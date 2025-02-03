import pytest
from shapely.geometry import Polygon
import geopandas as gpd
from src.processing_pipeline.spatial_analysis.create_grid import create_grid


@pytest.fixture
def sample_polygon():
    """Create a sample polygon for testing"""
    return Polygon([
        (-73.0, 42.0),  # bottom-left
        (-73.0, 42.1),  # top-left
        (-72.9, 42.1),  # top-right
        (-72.9, 42.0),  # bottom-right
        (-73.0, 42.0)   # close the polygon
    ])


def test_grid_creation_basic(sample_polygon):
    """Test basic grid creation with default parameters"""
    grid = create_grid(sample_polygon, cell_size=1000)

    # Check that we get a GeoDataFrame
    assert isinstance(grid, gpd.GeoDataFrame)

    # Check that the CRS is correct
    assert grid.crs == "EPSG:4326"

    # Check required columns
    required_columns = ['cell_id', 'geometry', 'cell_intersection_area',
                        'cell_area', 'cell_coverage_ratio']
    assert all(col in grid.columns for col in required_columns)

    # Check that we have some grid cells
    assert len(grid) > 0


def test_grid_metrics(sample_polygon):
    """Test the metrics calculated for the grid cells"""
    grid = create_grid(sample_polygon, cell_size=1000)

    # Check that intersection areas meet minimum requirement
    assert all(grid['cell_intersection_area'] >= 1000)

    # Check that coverage ratios are valid (between 0 and 1)
    assert all(0 <= ratio <= 1 for ratio in grid['cell_coverage_ratio'])

    # Check that all cell areas are positive
    assert all(grid['cell_area'] > 0)


def test_cell_size_effect(sample_polygon):
    """Test that different cell sizes produce expected results"""
    grid_large = create_grid(sample_polygon, cell_size=2000)
    grid_small = create_grid(sample_polygon, cell_size=1000)

    # Smaller cell size should result in more grid cells

    assert len(grid_small) > len(grid_large)
