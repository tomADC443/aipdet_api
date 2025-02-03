import pytest
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
import geopandas as gpd
from src.processing_pipeline.spatial_analysis.analyse_grid import analyze_grid_observations


@pytest.fixture
def sample_grid():
    """Create a sample grid for testing"""
    # Create a simple grid with two cells
    polygons = [
        Polygon([(-73.0, 42.0), (-73.0, 42.1), (-72.9, 42.1),
                (-72.9, 42.0), (-73.0, 42.0)]),
        Polygon([(-72.9, 42.0), (-72.9, 42.1),
                (-72.8, 42.1), (-72.8, 42.0), (-72.9, 42.0)])
    ]
    return gpd.GeoDataFrame(
        {'cell_id': ['cell_0_0', 'cell_0_1'],
         'geometry': polygons},
        crs="EPSG:4326"
    )


@pytest.fixture
def sample_observation():
    """Create a sample observation polygon"""
    return Polygon([
        (-73.0, 42.0),
        (-73.0, 42.1),
        (-72.8, 42.1),
        (-72.8, 42.0),
        (-73.0, 42.0)
    ])


def test_basic_analysis(sample_grid, sample_observation):
    """Test basic analysis with simple polygons"""
    result = analyze_grid_observations(
        sample_grid,
        [sample_observation],  # observed areas
        [sample_observation],  # ndvi areas
        [sample_observation]   # whc areas
    )

    # Check that we got back a GeoDataFrame
    assert isinstance(result, gpd.GeoDataFrame)

    # Check that we have the expected columns
    required_columns = [
        'total_observed_area',
        'total_ndvi_area',
        'total_whc_area',
        'ndvi_score',
        'whc_score'
    ]
    assert all(col in result.columns for col in required_columns)

    # Check CRS
    assert result.crs == "EPSG:4326"

    # Check that areas are positive
    assert all(result['total_observed_area'] >= 0)
    assert all(result['total_ndvi_area'] >= 0)
    assert all(result['total_whc_area'] >= 0)

    # Check that scores are between 0 and 1
    assert all(0 <= score <= 1 for score in result['ndvi_score'])
    assert all(0 <= score <= 1 for score in result['whc_score'])


def test_multipolygon_input(sample_grid):
    """Test handling of MultiPolygon inputs"""
    # Create a MultiPolygon from two polygons
    poly1 = Polygon([(-73.0, 42.0), (-73.0, 42.05),
                    (-72.9, 42.05), (-72.9, 42.0), (-73.0, 42.0)])
    poly2 = Polygon([(-72.9, 42.05), (-72.9, 42.1),
                    (-72.8, 42.1), (-72.8, 42.05), (-72.9, 42.05)])
    multi_poly = MultiPolygon([poly1, poly2])

    result = analyze_grid_observations(
        sample_grid,
        [multi_poly],
        [multi_poly],
        [multi_poly]
    )

    assert isinstance(result, gpd.GeoDataFrame)
    assert all(result['total_observed_area'] >= 0)


def test_empty_observations(sample_grid):
    """Test behavior with empty observation lists"""
    result = analyze_grid_observations(
        sample_grid,
        [],  # no observed areas
        [],  # no ndvi areas
        []   # no whc areas
    )

    assert isinstance(result, gpd.GeoDataFrame)
    assert all(result['total_observed_area'] == 0)
    assert all(result['total_ndvi_area'] == 0)
    assert all(result['total_whc_area'] == 0)
    assert all(result['ndvi_score'] == 0)
    assert all(result['whc_score'] == 0)


def test_invalid_geometry_handling(sample_grid):
    """Test handling of invalid geometries"""
    # Create an invalid polygon (self-intersecting)
    invalid_poly = Polygon([
        (-73.0, 42.0),
        (-72.8, 42.1),
        (-73.0, 42.1),
        (-72.8, 42.0),
        (-73.0, 42.0)
    ])

    # This should not raise an error due to the buffer(0) fix
    result = analyze_grid_observations(
        sample_grid,
        [invalid_poly],
        [invalid_poly],
        [invalid_poly]
    )

    assert isinstance(result, gpd.GeoDataFrame)
    assert all(result['total_observed_area'] >= 0)


if __name__ == '__main__':
    pytest.main([__file__])
