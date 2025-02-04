import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
import uuid
from src.main import app
from src.user.models import User
from src.user.router import get_settings, get_db
from src.user.constants import HTML_RESPONSE_SUCCESS, HTML_RESPONSE_ERROR

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
def mock_settings():
    """Create mock settings"""
    settings = Mock()
    settings.JWT_SECRET = "test_secret"
    settings.JWT_ALGORITHM = "HS256"
    settings.RUNNING_ENV = "development"
    settings.POSTMARK_API_TOKEN = "test_token"
    settings.BASE_URL = "http://test.com"
    settings.FRONTEND_BASE_URL = "http://test.com"

    # Override the get_settings dependency
    app.dependency_overrides[get_settings] = lambda: settings
    return settings


@pytest.fixture
def mock_requests(monkeypatch):
    """Mock external requests"""
    response = Mock()
    response.status_code = 200
    response.text = ""

    def mock_post(*args, **kwargs):
        return response

    monkeypatch.setattr('requests.post', mock_post)
    return response


def create_mock_user(**kwargs):
    """Helper function to create a mock user"""
    user = User()
    for key, value in kwargs.items():
        setattr(user, key, value)
    return user


def test_signup_success(client, mock_db, mock_settings, mock_requests):
    # Mock the database query that checks for existing user
    mock_scalar = Mock()
    mock_scalar.first.return_value = None
    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalar
    mock_db.execute.return_value = mock_result

    test_user = {
        "email": "test@example.com",
        "password": "testpassword123",
        "firstName": "Test",
        "lastName": "User"
    }

    response = client.post("/api/user/signup", json=test_user)
    assert response.status_code == 200, f"Response: {response.json()}"
    assert "userId" in response.json()
    assert mock_db.add.called
    assert mock_db.commit.called


def test_login_success(client, mock_db, mock_settings):
    # Create a real password hash
    password = "testpassword123"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Create a user with proper attributes
    mock_user = create_mock_user(
        id=uuid.uuid4(),
        email="test@example.com",
        password=hashed.decode('utf-8'),
        first_name="Test",
        last_name="User",
        verified=True
    )

    # Mock the database query
    mock_scalar = Mock()
    mock_scalar.first.return_value = mock_user
    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalar
    mock_db.execute.return_value = mock_result

    response = client.post("/api/user/login", json={
        "email": "test@example.com",
        "password": password
    })

    assert response.status_code == 200, f"Response: {response.json()}"
    assert "auth_token" in response.cookies
    assert response.json()["message"] == "Login successful."


def test_verify_email_success(client, mock_db):
    test_uuid = uuid.uuid4()
    test_secret = "test_secret"

    # Create a user with verify_secret
    mock_user = create_mock_user(
        id=test_uuid,
        verify_secret=test_secret,
        verified=False
    )
    mock_db.get.return_value = mock_user

    response = client.get(
        f"/api/user/verify-email?user={test_uuid}&secret={test_secret}")

    assert response.status_code == 200
    assert response.content.decode() == HTML_RESPONSE_SUCCESS
    assert mock_user.verified is True
    assert mock_db.commit.called


def test_verify_email_invalid(client, mock_db):
    test_uuid = uuid.uuid4()
    mock_db.get.return_value = None

    response = client.get(
        f"/api/user/verify-email?user={test_uuid}&secret=invalid_secret")

    assert response.status_code == 200
    assert response.content.decode() == HTML_RESPONSE_ERROR


def test_reset_password_success(client, mock_db, mock_requests):
    # Create a user for password reset
    mock_user = create_mock_user(
        id=uuid.uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User"
    )

    # Mock database query
    mock_scalar = Mock()
    mock_scalar.first.return_value = mock_user
    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalar
    mock_db.execute.return_value = mock_result

    response = client.post("/api/user/reset-password", json={
        "email": "test@example.com"
    })

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset initiated"
    assert mock_db.commit.called


def test_logout(client):
    response = client.post("/api/user/logout")

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
    assert "auth_token" in response.headers.get("set-cookie", "").lower()
    assert "max-age=0" in response.headers.get("set-cookie", "").lower()
