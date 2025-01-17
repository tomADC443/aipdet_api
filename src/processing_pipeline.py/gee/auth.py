import ee
import json
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


# def authenticate():
#     if config.ENVIRONMENT == Environment.LOCAL.value:
#         ee.Authenticate()
#         ee.Initialize(project=config.GOOGLE_PROJECT_ID)
#         print("Successfully authenticated - LOCAL Environment")
#     elif (
#         config.ENVIRONMENT == Environment.DEVELOPMENT.value
#         or config.ENVIRONMENT == Environment.PRODUCTION.value
#     ):
#           = config.GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT_EMAIL
#         credentials = ee.ServiceAccountCredentials(
#             service_account,
#             key_data=base64.b64decode(
#                 config.GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT_CREDENTIALS_B64
#             ).decode("utf-8"),
#         )
#         ee.Initialize(credentials)
#         print("Successfully authenticated - DEVELOPMENT/PRODUCTION Environment")
#     else:
#         raise ValueError("Invalid environment:" + config.ENVIRONMENT)
