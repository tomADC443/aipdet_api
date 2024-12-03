import ee
import os


def authenticate():
    service_account = "gee-675@aiap-436610.iam.gserviceaccount.com"
    credentials = ee.ServiceAccountCredentials(
        service_account, os.path.abspath("private-key-gee-service-account.json"))
    ee.Initialize(credentials)
