import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from src.report.utils import execute_safe_query, check_task_ownership
from src.task.models import Task
from sqlalchemy import select
from google.cloud import bigquery
import uuid


@pytest.fixture
def mock_bigquery_client():
    with patch('google.cloud.bigquery.Client') as mock_client:
        # Create a mock for query result
        mock_result = Mock()
        mock_result.result.return_value = [
            {"column1": "value1"},
            {"column2": "value2"}
        ]

        # Set up the mock client
        mock_client.from_service_account_info.return_value = Mock()
        mock_client.from_service_account_info.return_value.query.return_value = mock_result

        yield mock_client


@pytest.fixture
def mock_db_session():
    with patch('src.report.utils.SessionLocal') as mock_session:
        session_instance = Mock()
        mock_session.return_value = session_instance
        yield session_instance


def test_execute_safe_query_success(mock_bigquery_client):
    """Test successful query execution"""
    query = "SELECT * FROM table WHERE id = @param"
    params = {"param": "value"}

    result = execute_safe_query(query, params)

    # Verify client was created with correct settings
    mock_bigquery_client.from_service_account_info.assert_called_once()

    # Verify query was executed with parameters
    mock_client = mock_bigquery_client.from_service_account_info.return_value
    mock_client.query.assert_called_once()

    # Verify client was closed
    mock_client.close.assert_called_once()


def test_execute_safe_query_error(mock_bigquery_client):
    """Test query execution with error"""
    query = "SELECT * FROM table WHERE id = @param"
    params = {"param": "value"}

    # Set up mock to raise an error
    mock_client = mock_bigquery_client.from_service_account_info.return_value
    mock_client.query.side_effect = Exception("Query failed")

    with pytest.raises(Exception):
        execute_safe_query(query, params)

    # Verify client was still closed even after error
    mock_client.close.assert_called_once()


@pytest.fixture
def sample_task():
    return Task(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        name="Test Task",
        is_public=False
    )


def test_check_task_ownership_owner(mock_db_session, sample_task):
    """Test when user owns the task"""
    # Set up mock database response
    mock_scalar = Mock()
    mock_scalar.first.return_value = sample_task
    mock_db_session.execute.return_value.scalars.return_value = mock_scalar

    # Should not raise any exception
    check_task_ownership(sample_task.id, sample_task.user_id)

    # Verify database was queried correctly
    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.close.assert_called_once()


def test_check_task_ownership_public_task(mock_db_session, sample_task):
    """Test when task is public but user doesn't own it"""
    # Modify task to be public
    sample_task.is_public = True

    # Set up mock database response
    mock_scalar = Mock()
    mock_scalar.first.return_value = sample_task
    mock_db_session.execute.return_value.scalars.return_value = mock_scalar

    # Should not raise any exception
    check_task_ownership(sample_task.id, "different-user-id")

    mock_db_session.close.assert_called_once()


def test_check_task_ownership_unauthorized(mock_db_session, sample_task):
    """Test when user doesn't own the task and it's not public"""
    # Set up mock database response
    mock_scalar = Mock()
    mock_scalar.first.return_value = sample_task
    mock_db_session.execute.return_value.scalars.return_value = mock_scalar

    with pytest.raises(HTTPException) as exc_info:
        check_task_ownership(sample_task.id, "different-user-id")

    assert exc_info.value.status_code == 403
    mock_db_session.close.assert_called_once()


def test_check_task_ownership_not_found(mock_db_session):
    """Test when task doesn't exist"""
    # Set up mock database response for non-existent task
    mock_scalar = Mock()
    mock_scalar.first.return_value = None
    mock_db_session.execute.return_value.scalars.return_value = mock_scalar

    with pytest.raises(HTTPException) as exc_info:
        check_task_ownership("non-existent-id", "any-user-id")

    assert exc_info.value.status_code == 404
    mock_db_session.close.assert_called_once()


def test_check_task_ownership_db_error(mock_db_session):
    """Test database error handling"""
    # Set up mock to raise an error
    mock_db_session.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception):
        check_task_ownership("task-id", "user-id")

    # Verify database connection was closed even after error
    mock_db_session.close.assert_called_once()
