import pytest
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from src.database import SessionLocal
from src.aoi.models import AOI
from src.user.models import User
from sqlalchemy import text
import bcrypt


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    """Helper function to hash password"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


@pytest.mark.integration
def test_postgres_connection(db_session: Session):
    """Test PostgreSQL connection by creating and deleting a test AOI"""

    # First create a test user
    test_user_id = uuid.uuid4()
    test_user = User(
        id=test_user_id,
        email='test_tom@tom.com',
        first_name='Test',
        last_name='User',
        password=hash_password('test_password'),
        verified=False,
        created_at=datetime.utcnow()
    )

    # Create test AOI
    test_aoi = AOI(
        id=uuid.uuid4(),
        user_id=test_user_id,
        name="Integration Test AOI",
        description="Test AOI for integration testing",
        geometry={
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
            }
        },
        created_at=datetime.utcnow()
    )

    aoi_id = test_aoi.id  # Store ID for cleanup

    try:
        # First insert the user
        db_session.add(test_user)
        db_session.commit()

        # Then insert the AOI
        db_session.add(test_aoi)
        db_session.commit()

        # Verify AOI insertion
        result = db_session.execute(
            text("SELECT COUNT(*) FROM aoi WHERE id = :id"),
            {"id": aoi_id}
        ).scalar()
        assert result == 1, "Test AOI was not inserted correctly"

        # Verify AOI data integrity
        aoi_data = db_session.execute(
            text("SELECT name, description FROM aoi WHERE id = :id"),
            {"id": aoi_id}
        ).first()
        assert aoi_data.name == test_aoi.name, "AOI name does not match"
        assert aoi_data.description == test_aoi.description, "AOI description does not match"

    finally:
        # Clean up in reverse order (AOI first, then user)
        db_session.rollback()  # Reset any failed transaction

        # Start new transaction for cleanup
        db_session.begin()

        try:
            # Delete using raw SQL to avoid ORM issues
            db_session.execute(
                text("DELETE FROM aoi WHERE id = :id"),
                {"id": aoi_id}
            )
            db_session.execute(
                text("DELETE FROM \"user\" WHERE id = :id"),
                {"id": test_user_id}
            )
            db_session.commit()

            # Verify cleanup with new session to avoid stale data
            verify_session = SessionLocal()
            try:
                # Verify AOI cleanup
                result = verify_session.execute(
                    text("SELECT COUNT(*) FROM aoi WHERE id = :id"),
                    {"id": aoi_id}
                ).scalar()
                assert result == 0, "Test AOI was not cleaned up correctly"

                # Verify user cleanup
                result = verify_session.execute(
                    text("SELECT COUNT(*) FROM \"user\" WHERE id = :id"),
                    {"id": test_user_id}
                ).scalar()
                assert result == 0, "Test user was not cleaned up correctly"
            finally:
                verify_session.close()

        except Exception as e:
            db_session.rollback()
            raise e
