from typing import Any
from src.config import get_settings
from google.cloud import bigquery
import json
from src.task.models import Task, TaskProcesses
from sqlalchemy import select, and_, update
from src.database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

settings = get_settings()


def execute_safe_query(
    query: str,
    params: dict[str, Any]
) -> bigquery.job.QueryJob:
    """Execute a BigQuery query with safe parameterization"""

    client = bigquery.Client.from_service_account_info(
        json.loads(settings.AIPDET_BE_SA_GCP)
    )

    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(name, "STRING", value)
                for name, value in params.items()
            ]
        )
        return client.query(query, job_config=job_config).result()
    finally:
        client.close()


def check_task_ownership(
    task_id: str,
    user_id: str
) -> bool:
    """Check if the user owns the task/ the task is public"""

    try:
        db: Session = SessionLocal()

        task = db.execute(select(Task).where(
            Task.id == task_id)).scalars().first()
        db.commit()

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if str(task.user_id) == str(user_id):
            return

        if not task.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
            )
    finally:
        db.close()
