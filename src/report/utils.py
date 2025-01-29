from typing import Any
from src.config import get_settings
from google.cloud import bigquery
import json


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
