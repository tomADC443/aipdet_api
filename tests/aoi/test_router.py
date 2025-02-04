from src.task.models import Task
import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
import uuid
from src.main import app
from src.aoi.models import AOI
from src.database import get_db
from src.dependencies import get_current_user
from datetime import datetime


# Create test client


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


def create_mock_aoi(**kwargs):
    """Helper function to create a mock AOI"""
    aoi = AOI(
        id=kwargs.get('id', uuid.uuid4()),
        name=kwargs.get('name', 'Test AOI'),
        description=kwargs.get('description', 'This is a test AOI'),
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


def create_mock_task(**kwargs):
    """Helper function to create a mock Task"""
    task = Task(
        id=kwargs.get('id', uuid.uuid4()),
        aoi_id=kwargs.get('aoi_id'),
        name=kwargs.get('name', 'Test Task'),
        status=kwargs.get('status', 'Processing'),
        created_at=kwargs.get('created_at', datetime.utcnow())
    )
    return task


def test_create_aoi_success(client, mock_db, mock_current_user):
    test_aoi_data = {
        "name": "Test AOI",
        "description": "This is a test AOI",
        "geometry": {
            "type": "Feature",  # Change to Feature
            "geometry": {  # Add geometry.geometry
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
            }
        }
    }

    response = client.post("/api/aoi", json=test_aoi_data)
    assert response.status_code == 200, f"Response: {response.json()}"
    assert response.json() == {"message": "AOI created successfully", }
    assert mock_db.add.called
    assert mock_db.commit.called


def test_get_aois_success(client, mock_db, mock_current_user):
    # Create mock AOIs and Tasks
    mock_aoi_1 = create_mock_aoi(id=uuid.uuid4(), name="AOI 1")
    mock_task_1 = create_mock_task(id=uuid.uuid4(), aoi_id=mock_aoi_1.id)
    mock_aoi_2 = create_mock_aoi(id=uuid.uuid4(), name="AOI 2")

    # Mock the database query
    mock_db.execute.return_value.all.return_value = [
        (mock_aoi_1, mock_task_1),
        (mock_aoi_2, None)
    ]

    response = client.get("/api/aois")
    assert response.status_code == 200, f"Response: {response.json()}"
    assert len(response.json()["aois"]) == 2
    assert response.json()["aois"][0]["hasTask"] == True
    assert response.json()["aois"][1]["hasTask"] == False


def test_delete_aoi_success(client, mock_db, mock_current_user):
    import json

    # Create mock AOI
    mock_aoi = create_mock_aoi(id=uuid.uuid4(), name="AOI to delete")

    # Mock the database query
    mock_db.execute.return_value.first.return_value = (mock_aoi, None)

    response = client.request("delete",  # this should be client.delete instead of client.request, but currently thats not possible (https://github.com/fastapi/fastapi/issues/5649)  (also in the next test :)) I will fix this in the future and change the aoi router to accept the id as a query parameter
                              "/api/aoi",
                              data=json.dumps({"id": str(mock_aoi.id)}),
                              headers={"Content-Type": "application/json"}
                              )

    assert response.status_code == 200, f"Response: {response.json()}"
    assert response.json() == {
        "message": "AOI successfully deleted.",
        "id": str(mock_aoi.id)
    }
    assert mock_db.delete.called
    assert mock_db.commit.called


def test_delete_aoi_with_task(client, mock_db, mock_current_user):
    # Create mock AOI and Task
    mock_aoi = create_mock_aoi(id=uuid.uuid4(), name="AOI with task")
    mock_task = create_mock_task(id=uuid.uuid4(), aoi_id=mock_aoi.id)

    # Mock the database query
    mock_db.execute.return_value.first.return_value = (mock_aoi, mock_task)

    response = client.request("delete", "/api/aoi",
                              json={"id": str(mock_aoi.id)})
    assert response.status_code == 400, f"Response: {response.json()}"
    assert response.json() == {
        "detail": "Do not delete AOIs that are connected to tasks."
    }
