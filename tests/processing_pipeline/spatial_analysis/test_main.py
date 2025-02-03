import pytest
from unittest.mock import Mock, patch
from shapely.geometry import Polygon, MultiPolygon
import json
from src.processing_pipeline.spatial_analysis.main import (
    get_spatial_analysis,
    extract_geometry,
    upload_grid_to_bigquery
)


@pytest.fixture
def sample_polygon():
    """Create a sample polygon for testing"""
    return Polygon([
        (-73.0, 42.0),
        (-73.0, 42.1),
        (-72.9, 42.1),
        (-72.9, 42.0),
        (-73.0, 42.0)
    ])


@pytest.fixture
def sample_query_result():
    """Create sample query results mimicking BigQuery response"""
    class Row:
        def __init__(self, valid_area, ndvi, whc, date):
            self.valid_area = valid_area
            self.NDVI = ndvi
            self.WHC = whc
            self.date = date

    valid_area = {
        "type": "Polygon",
        "coordinates": [[
            [-73.0, 42.0],
            [-73.0, 42.1],
            [-72.9, 42.1],
            [-72.9, 42.0],
            [-73.0, 42.0]
        ]]
    }

    ndvi_area = {
        "type": "Polygon",
        "coordinates": [[
            [-73.0, 42.0],
            [-73.0, 42.05],
            [-72.95, 42.05],
            [-72.95, 42.0],
            [-73.0, 42.0]
        ]]
    }

    whc_area = {
        "type": "Polygon",
        "coordinates": [[
            [-72.95, 42.0],
            [-72.95, 42.05],
            [-72.9, 42.05],
            [-72.9, 42.0],
            [-72.95, 42.0]
        ]]
    }

    return [Row(
        json.dumps(valid_area),
        json.dumps(ndvi_area),
        json.dumps(whc_area),
        "2024-02-03"
    )]


@pytest.fixture
def mock_bigquery_client():
    """Mock BigQuery client"""
    with patch('google.cloud.bigquery.Client') as mock_client:
        mock_instance = Mock()
        mock_client.from_service_account_info.return_value = mock_instance
        yield mock_instance


def test_extract_geometry_polygon():
    """Test extraction of Polygon geometries"""
    geojson = {
        "type": "Polygon",
        "coordinates": [[
            [-73.0, 42.0],
            [-73.0, 42.1],
            [-72.9, 42.1],
            [-72.9, 42.0],
            [-73.0, 42.0]
        ]]
    }

    result = extract_geometry(geojson)
    assert isinstance(result, Polygon)
    assert result.is_valid


def test_extract_geometry_multipolygon():
    """Test extraction of MultiPolygon geometries"""
    geojson = {
        "type": "MultiPolygon",
        "coordinates": [
            [[
                [-73.0, 42.0],
                [-73.0, 42.1],
                [-72.9, 42.1],
                [-72.9, 42.0],
                [-73.0, 42.0]
            ]],
            [[
                [-72.8, 42.0],
                [-72.8, 42.1],
                [-72.7, 42.1],
                [-72.7, 42.0],
                [-72.8, 42.0]
            ]]
        ]
    }

    result = extract_geometry(geojson)
    assert isinstance(result, MultiPolygon)
    assert result.is_valid
    assert len(result.geoms) == 2


@patch('src.processing_pipeline.spatial_analysis.main.execute_safe_query')
@patch('src.processing_pipeline.spatial_analysis.main.upload_grid_to_bigquery')
def test_get_spatial_analysis(mock_upload, mock_execute_query, sample_polygon, sample_query_result, mock_bigquery_client):
    """Test the main spatial analysis function"""
    # Setup mock
    mock_execute_query.return_value = sample_query_result
    mock_upload.return_value = None

    try:
        # Run analysis
        result = get_spatial_analysis("test_id", sample_polygon)

        # Verify the result is JSON
        assert isinstance(result, str)
        result_dict = json.loads(result)

        # Check that features exist in the result
        assert "features" in result_dict
        assert len(result_dict["features"]) > 0

        # Verify query was executed
        mock_execute_query.assert_called_once()

        # Verify BigQuery upload was attempted
        mock_upload.assert_called_once()
    except Exception as e:
        pytest.fail(f"Test failed with exception: {str(e)}")


@patch('src.processing_pipeline.spatial_analysis.main.execute_safe_query')
@patch('src.processing_pipeline.spatial_analysis.main.upload_grid_to_bigquery')
def test_get_spatial_analysis_empty_result(mock_upload, mock_execute_query, sample_polygon, mock_bigquery_client):
    """Test handling of empty query results"""
    # Setup mocks
    mock_execute_query.return_value = []
    mock_upload.return_value = None

    try:
        # Run analysis
        result = get_spatial_analysis("test_id", sample_polygon)

        # Verify we still get valid JSON output
        assert isinstance(result, str)
        result_dict = json.loads(result)
        assert "features" in result_dict

        # Verify interactions
        mock_execute_query.assert_called_once()
        mock_upload.assert_called_once()
    except Exception as e:
        pytest.fail(f"Test failed with exception: {str(e)}")


def test_extract_geometry_invalid_type():
    """Test handling of invalid GeoJSON type"""
    geojson = {
        "type": "Point",
        "coordinates": [-73.0, 42.0]
    }

    with pytest.raises(ValueError, match="Must be 'Polygon' or 'Multipolygon'"):
        extract_geometry(geojson)


@patch('google.cloud.bigquery.LoadJobConfig')
def test_upload_grid_to_bigquery(mock_job_config, mock_bigquery_client, sample_polygon):
    """Test BigQuery upload functionality"""
    import geopandas as gpd

    # Create sample GeoDataFrame
    gdf = gpd.GeoDataFrame(
        {
            'process_id': ['test_id'],
            'cell_id': ['cell_0'],
            'geometry': [sample_polygon]
        },
        crs="EPSG:4326"
    )

    # Add required columns
    gdf['cell_area'] = 1000.0
    gdf['total_observed_area'] = 500.0
    gdf['cell_intersection_area'] = 500.0
    gdf['cell_coverage_ratio'] = 0.5
    gdf['total_ndvi_area'] = 250.0
    gdf['ndvi_score'] = 0.5
    gdf['total_whc_area'] = 250.0
    gdf['whc_score'] = 0.5

    # Test upload
    upload_grid_to_bigquery(gdf)

    # Verify client was used correctly
    mock_bigquery_client.load_table_from_dataframe.assert_called_once()
    mock_bigquery_client.close.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])
