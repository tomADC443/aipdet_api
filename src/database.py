from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from google.cloud.sql.connector import Connector, IPTypes
from google.oauth2 import service_account
import os
import json
from src.config import get_settings

settings = get_settings()

# Initialize the Cloud SQL Python Connector
connector = Connector(credentials=service_account.Credentials.from_service_account_info(
    json.loads(settings.AIPDET_FE_SA_GCP)))


def get_connection():
    """
    Create a secure connection to the PostgreSQL database using the
    Cloud SQL Python Connector and a service account key JSON.
    """
    return connector.connect(
        "aiap-436610:europe-west3:aipdetdb",  # Cloud SQL Instance Connection Name
        "pg8000",
        user="aipdet-fe@aiap-436610.iam",
        db="postgres",
        enable_iam_auth=True,
        ip_type="public",  # "private" for private IP

    )


# Create SQLAlchemy engine
engine = create_engine(
    "postgresql+pg8000://",  # SQLAlchemy dialect for PostgreSQL with pg8000
    creator=get_connection,  # Use the connector to create connections
    future=True,  # SQLAlchemy 2.0 style
)

# Create a session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base class for SQLAlchemy models
Base = declarative_base()

# Dependency to provide DB sessions


def get_db():
    """
    Dependency to provide database session for FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Cleanup Connector on application shutdown


def close_connector():
    connector.close()
