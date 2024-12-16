import ee
from datetime import datetime


def get_imagery(
    aoi: ee.Geometry,
    start_date: datetime,
    end_date: datetime,
) -> ee.ImageCollection:

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start_date_str, end_date_str)
        .filterBounds(aoi)
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 95))
    )
    return collection
