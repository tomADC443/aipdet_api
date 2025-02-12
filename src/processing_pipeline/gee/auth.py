import ee
import base64
from src.config import get_settings
settings = get_settings()


def authenticate():
    service_account = "gee-675@aiap-436610.iam.gserviceaccount.com"
    credentials = ee.ServiceAccountCredentials(
        service_account,
        key_data=base64.b64decode(
            settings.GEE_SA_GCP
        ).decode("utf-8")
    )
    ee.Initialize(credentials)
