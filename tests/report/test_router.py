import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import uuid
from datetime import datetime
from src.main import app
from src.database import get_db
from src.dependencies import get_current_user
from fastapi import HTTPException, status


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


@pytest.fixture
def mock_db():
    mock = Mock()
    mock.close.return_value = None
    app.dependency_overrides[get_db] = lambda: mock
    return mock


@pytest.fixture
def mock_current_user():
    user = {
        'sub': str(uuid.uuid4()),
        'email': 'test@example.com',
        'firstName': 'Test',
        'lastName': 'User'
    }
    app.dependency_overrides[get_current_user] = lambda: user
    return user


@pytest.fixture
def mock_execute_query():
    with patch('src.report.router.execute_safe_query') as mock:
        yield mock


@pytest.fixture
def mock_task_ownership():
    with patch('src.report.router.check_task_ownership') as mock:
        mock.return_value = True  # Task ownership check passes
        yield mock


def test_get_distinct_images_count_success(client, mock_db, mock_current_user, mock_execute_query, mock_task_ownership):
    task_id = str(uuid.uuid4())
    mock_execute_query.return_value = iter([(10,)])

    response = client.get(
        f"/api/report/number-total-distinct-images?taskId={task_id}")

    assert response.status_code == 200, f"Response: {response.json()}"
    assert response.json() == {"count": 10}
    mock_execute_query.assert_called_once()
    mock_task_ownership.assert_called_once_with(
        task_id, mock_current_user['sub'])


def test_get_temporal_range_success(client, mock_db, mock_current_user, mock_execute_query, mock_task_ownership):
    task_id = str(uuid.uuid4())
    mock_result = Mock()
    mock_result.from_date = datetime(2024, 1, 1)
    mock_result.to_date = datetime(2024, 2, 1)
    mock_execute_query.return_value = iter([mock_result])

    response = client.get(f"/api/report/temporal-range?taskId={task_id}")

    assert response.status_code == 200, f"Response: {response.json()}"
    data = response.json()
    assert "fromDate" in data
    assert "toDate" in data
    mock_task_ownership.assert_called_once_with(
        task_id, mock_current_user['sub'])


def test_get_total_observed_area_success(client, mock_db, mock_current_user, mock_execute_query, mock_task_ownership):
    task_id = str(uuid.uuid4())
    mock_result = Mock()
    mock_result.area = 1000.0
    mock_execute_query.return_value = iter([mock_result])

    response = client.get(f"/api/report/total-observed-area?taskId={task_id}")

    assert response.status_code == 200, f"Response: {response.json()}"
    assert response.json() == {"area": 1000.0}
    mock_task_ownership.assert_called_once_with(
        task_id, mock_current_user['sub'])


def test_unauthorized_access(client, mock_db, mock_current_user, mock_execute_query, mock_task_ownership):
    task_id = str(uuid.uuid4())
    # Simulate unauthorized access
    mock_task_ownership.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to access this task."
    )

    response = client.get(
        f"/api/report/number-total-distinct-images?taskId={task_id}")

    assert response.status_code == 403
    assert response.json()[
        "detail"] == "You don't have permission to access this task."


def test_get_spatial_analysis_success(client, mock_db, mock_current_user, mock_execute_query, mock_task_ownership):
    task_id = str(uuid.uuid4())
    mock_row = Mock()
    mock_row.process_id = str(uuid.uuid4())
    mock_row.cell_id = "cell1"
    mock_row.cell_area = 100.0
    mock_row.cell_intersection_area = 50.0
    mock_row.cell_coverage_ratio = 0.5
    mock_row.total_observed_area = 1000.0
    mock_row.total_ndvi_area = 500.0
    mock_row.ndvi_score = 0.75
    mock_row.total_whc_area = 250.0
    mock_row.whc_score = 0.25
    mock_row.geometry = '{"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]}'

    mock_execute_query.return_value = iter([mock_row])

    response = client.get(f"/api/report/spatial-analysis?taskId={task_id}")

    assert response.status_code == 200, f"Response: {response.json()}"
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    mock_task_ownership.assert_called_once_with(
        task_id, mock_current_user['sub'])


def test_get_available_dates_success(client, mock_db, mock_current_user, mock_execute_query, mock_task_ownership):
    task_id = str(uuid.uuid4())
    mock_row1 = Mock()
    mock_row1.date = datetime(2024, 1, 1)
    mock_row2 = Mock()
    mock_row2.date = datetime(2024, 1, 2)
    mock_execute_query.return_value = iter([mock_row1, mock_row2])

    response = client.get(f"/api/report/available-dates?taskId={task_id}")

    assert response.status_code == 200, f"Response: {response.json()}"
    data = response.json()
    assert len(data["dates"]) == 2
    mock_task_ownership.assert_called_once_with(
        task_id, mock_current_user['sub'])


def test_get_analysis_record_success(client, mock_db, mock_current_user, mock_execute_query, mock_task_ownership):
    task_id = str(uuid.uuid4())
    date_string = "2024-01-01"
    mock_row = Mock()
    mock_row.observed_area = '{"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]}'
    mock_row.ndvi_area = '{"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]}'
    mock_row.whc_area = '{"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]}'

    mock_execute_query.return_value = iter([mock_row])

    response = client.get(
        f"/api/report/analysis-record?taskId={task_id}&dateString={date_string}")

    assert response.status_code == 200, f"Response: {response.json()}"
    data = response.json()
    assert len(data["observed_areas"]) == 1
    assert len(data["ndvi_areas"]) == 1
    assert len(data["whc_areas"]) == 1
    assert data["dateString"] == date_string
    mock_task_ownership.assert_called_once_with(
        task_id, mock_current_user['sub'])


def test_endpoint_server_error(client, mock_db, mock_current_user, mock_execute_query, mock_task_ownership):
    task_id = str(uuid.uuid4())
    # Make sure task ownership check passes but database operation fails
    mock_task_ownership.return_value = True
    mock_execute_query.side_effect = Exception("Database error")

    response = client.get(
        f"/api/report/number-total-distinct-images?taskId={task_id}")

    assert response.status_code == 500, f"Response: {response.json()}"
    mock_task_ownership.assert_called_once_with(
        task_id, mock_current_user['sub'])
