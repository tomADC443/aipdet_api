import pytest
from datetime import datetime
import uuid
from src.report.utils import execute_safe_query
from src.config import get_settings

settings = get_settings()


@pytest.mark.integration
def test_bigquery_connection():
    """Test BigQuery connection by inserting and deleting a test record"""

    # Generate unique test data
    test_id = str(uuid.uuid4())
    # Format datetime as DATE string (YYYY-MM-DD)
    test_date = datetime.utcnow().strftime('%Y-%m-%d')

    verify_query = """
        SELECT COUNT(*) as count
        FROM `{table}`
        WHERE process_id = @process_id
    """.format(table=settings.DATABASE_REPORT_TABLE)

    insert_query = """
        INSERT INTO `{table}` (
            process_id,
            utc_capture_start,
            image_id
        ) VALUES (
            @process_id,
            DATE(@capture_date),
            @image_id
        )
    """.format(table=settings.DATABASE_REPORT_TABLE)

    cleanup_query = """
        DELETE FROM `{table}`
        WHERE process_id = @process_id
    """.format(table=settings.DATABASE_REPORT_TABLE)

    try:
        # Insert test record
        execute_safe_query(
            query=insert_query,
            params={
                "process_id": test_id,
                "capture_date": test_date,
                "image_id": "test_image"
            }
        )

        # Verify insertion
        result = execute_safe_query(
            query=verify_query,
            params={"process_id": test_id}
        )
        count = next(result)[0]
        assert count == 1, "Test record was not inserted correctly"

    finally:
        # Clean up test record
        execute_safe_query(
            query=cleanup_query,
            params={"process_id": test_id}
        )

        # Verify cleanup
        result = execute_safe_query(
            query=verify_query,
            params={"process_id": test_id}
        )
        count = next(result)[0]
        assert count == 0, "Test record was not cleaned up correctly"
