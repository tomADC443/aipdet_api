import uuid
from src.dependencies import get_current_user
import pytest
from fastapi.testclient import TestClient
from src.main import app  # Ensure this is the correct import for FastAPI app instance
from src.database import get_db
from sqlalchemy.orm import Session
from unittest.mock import Mock
import json
from src.task.models import Task, TaskProcesses
from src.task.constants import Task_Status
from datetime import datetime
from sqlalchemy import delete


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
        # ✅ Ensure deletable status
        status=kwargs.get('status', Task_Status.Successful.value),
        created_at=kwargs.get('created_at', datetime.utcnow())
    )
    return task


def test_delete_task_success(client, mock_db, mock_current_user):
    mock_task = create_mock_task(id="1")
    mock_db.execute.return_value = Mock()

    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_task

    response = client.request("delete",
                              "/api/task",

                              data=json.dumps({"id": "1"}),
                              headers={"Content-Type": "application/json"})

    assert response.status_code == 200, f"Response: {response.json()}"
