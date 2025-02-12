from src.aoi.models import AOI
import uuid
from src.dependencies import get_current_user
import pytest
from fastapi.testclient import TestClient
from src.main import app  # Ensure this is the correct import for FastAPI app instance
from src.database import get_db
from unittest.mock import Mock
import json
from src.task.models import Task
from src.task.constants import Task_Status
from datetime import datetime
from unittest.mock import patch


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_dependencies():
    """Override FastAPI dependencies for testing"""
    app.dependency_overrides = {}  # Clear any existing overrides
    yield
    app.dependency_overrides = {}  # Clean up after test


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    mock = Mock()
    mock.close.return_value = None

    # Override the get_db dependency
    app.dependency_overrides[get_db] = lambda: mock
    return mock


@pytest.fixture
def mock_current_user():
    """Create a mock current user"""
    user = {
        'sub': str(uuid.uuid4()),
        'email': 'test@example.com',
        'firstName': 'Test',
        'lastName': 'User'
    }

    # Override the get_current_user dependency
    app.dependency_overrides[get_current_user] = lambda: user
    return user


def create_mock_task(**kwargs):
    """Helper function to create a mock Task"""
    task = Task(
        id=kwargs.get('id', str(uuid.uuid4())),  # Ensure ID is a string
        aoi_id=kwargs.get('aoi_id', uuid.uuid4()),
        name=kwargs.get('name', 'Test Task'),
        # Ensure deletable status
        status=kwargs.get('status', Task_Status.Successful.value),
        created_at=kwargs.get('created_at', datetime.utcnow()),
        is_public=kwargs.get('is_public', False)
    )
    return task


def test_delete_task_success(client, mock_db, mock_current_user):
    # Create mock task with UUID
    task_id = uuid.uuid4()
    mock_task = create_mock_task(
        id=task_id, status=Task_Status.Successful.value)

    # Set up mock for the initial task query (first execute call)
    mock_select_result = Mock()
    mock_select_result.scalars = Mock()
    mock_select_result.scalars.return_value = Mock()
    mock_select_result.scalars.return_value.first = Mock(
        return_value=mock_task)

    # Set up mock for the delete query (second execute call)
    mock_delete_result = Mock()

    # Set up the mock for execute with multiple return values
    mock_db.execute = Mock(
        side_effect=[mock_select_result, mock_delete_result])

    response = client.request(
        "delete",
        "/api/task",
        data=json.dumps({"id": str(task_id)}),
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200, f"Response: {response.json()}"

    # Verify both database calls were made in correct order
    assert mock_db.execute.call_count >= 2

    # First call should be the SELECT query
    first_call_args = mock_db.execute.call_args_list[0][0][0]
    assert str(first_call_args).startswith('SELECT')
    assert 'FROM task' in str(first_call_args)

    # Second call should be the DELETE query
    second_call_args = mock_db.execute.call_args_list[1][0][0]
    assert str(second_call_args).startswith('DELETE FROM task_processes')

    assert mock_db.close.called


def create_mock_aoi(**kwargs):
    """Helper function to create a mock AOI"""
    aoi = AOI(
        id=kwargs.get('id', uuid.uuid4()),
        name=kwargs.get('name', 'Test AOI'),
        description=kwargs.get('description', 'Test Description'),
        geometry=kwargs.get('geometry', {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
            }
        }),
        created_at=kwargs.get('created_at', datetime.utcnow())
    )
    return aoi


def test_get_tasks_success(client, mock_db, mock_current_user):
    # Create mock tasks and AOIs
    aoi1 = create_mock_aoi(id=uuid.uuid4())
    task1 = create_mock_task(aoi_id=aoi1.id)
    aoi2 = create_mock_aoi(id=uuid.uuid4())
    task2 = create_mock_task(aoi_id=aoi2.id)

    # Mock the database query
    mock_query_result = Mock()
    mock_query_result.unique = Mock()
    mock_query_result.unique.return_value = Mock()
    mock_query_result.unique.return_value.all = Mock(return_value=[
        (task1, aoi1),
        (task2, aoi2)
    ])
    mock_db.execute = Mock(return_value=mock_query_result)

    response = client.get("/api/tasks")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["aoi"]["id"] == str(aoi1.id)
    assert data[1]["aoi"]["id"] == str(aoi2.id)
    assert mock_db.close.called


def test_get_public_tasks_success(client, mock_db, mock_current_user):
    # Create mock tasks and AOIs
    aoi1 = create_mock_aoi(id=uuid.uuid4())
    task1 = create_mock_task(aoi_id=aoi1.id, is_public=True)

    # Mock the database query
    mock_query_result = Mock()
    mock_query_result.unique = Mock()
    mock_query_result.unique.return_value = Mock()
    mock_query_result.unique.return_value.all = Mock(return_value=[
        (task1, aoi1)
    ])
    mock_db.execute = Mock(return_value=mock_query_result)

    response = client.get("/api/tasks/public")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["aoi"]["id"] == str(aoi1.id)


def test_create_task_success(client, mock_db, mock_current_user):
    # Create mock AOI
    aoi_id = uuid.uuid4()
    mock_aoi = create_mock_aoi(id=aoi_id)

    # Set up multiple mock responses for different database operations
    mock_aoi_query = Mock()
    mock_aoi_query.scalar = Mock(return_value=mock_aoi)

    mock_task_query = Mock()
    mock_task_query.scalar = Mock()

    # Set up the mock for execute with multiple return values
    mock_db.execute = Mock(side_effect=[mock_aoi_query])

    # Mock the add operation
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()

    task_data = {
        "name": "New Task",
        "aoiId": str(aoi_id),
        "isPublic": True
    }

    # Mock the background tasks
    def mock_background_task():
        pass

    with patch('fastapi.BackgroundTasks.add_task') as mock_add_task:
        response = client.post("/api/task", json=task_data)

        assert response.status_code == 200, f"Response: {response.json()}"
        assert response.json()[
            "message"] == "Task created successfully. Processing started."

        # Verify database operations
        assert mock_db.execute.called
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called
        assert mock_db.close.called


def test_create_task_aoi_not_found(client, mock_db, mock_current_user):
    # Mock database query returning None for AOI
    mock_select_result = Mock()
    mock_select_result.scalar = Mock(return_value=None)
    mock_db.execute = Mock(return_value=mock_select_result)

    task_data = {
        "name": "New Task",
        "aoiId": str(uuid.uuid4()),
        "isPublic": True
    }

    response = client.post("/api/task", json=task_data)

    assert response.status_code == 404
    assert response.json()["detail"] == "AOI not found."
    assert mock_db.close.called


def test_delete_task_not_found(client, mock_db, mock_current_user):
    # Set up mock to return None for task query
    mock_query_result = Mock()
    mock_query_result.scalars = Mock()
    mock_query_result.scalars.return_value = Mock()
    mock_query_result.scalars.return_value.first = Mock(return_value=None)
    mock_db.execute = Mock(return_value=mock_query_result)

    response = client.request(
        "delete",
        "/api/task",
        data=json.dumps({"id": str(uuid.uuid4())}),
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 404
    assert response.json()[
        "detail"] == "Task not found or you don't have permission to delete it."


def test_delete_task_still_processing(client, mock_db, mock_current_user):
    # Create mock task with processing status
    task_id = uuid.uuid4()
    mock_task = create_mock_task(
        id=task_id,
        status=Task_Status.Processing.value
    )

    mock_query_result = Mock()
    mock_query_result.scalars = Mock()
    mock_query_result.scalars.return_value = Mock()
    mock_query_result.scalars.return_value.first = Mock(return_value=mock_task)
    mock_db.execute = Mock(return_value=mock_query_result)

    response = client.request(
        "delete",
        "/api/task",
        data=json.dumps({"id": str(task_id)}),
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert response.json()[
        "detail"] == "Task cannot be deleted because it is still processing."
