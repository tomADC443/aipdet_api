

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.config import get_settings
from google.cloud import bigquery
from src.report.schemas import task_id_parameter
from src.dependencies import get_current_user, login_required


report_router = APIRouter()
settings = get_settings()


@login_required
@report_router.get("/number-total-distinct-images")
def get_distinct_images_count(
    task_id: str = task_id_parameter,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = (
        f'SELECT COUNT(DISTINCT image_id)\n'
        f'FROM `{settings.DATABASE_REPORT_TABLE}` \n'
        f'WHERE process_id = \'{task_id}\''
    )

    try:
        client = bigquery.Client.from_service_account_json(
            'private-key-bigQuery-account.json'
        )
        query_job = client.query(query)
        result = query_job.result()
        print(result)
        row = next(result, None)
        print(row)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found."
            )

        return {"count": row[0]}

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
