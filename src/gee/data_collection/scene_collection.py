import ee
from datetime import datetime
from typing import Union


def get_imagery(aoi: ee.Geometry.Polygon, start_date: Union[datetime, str], end_date: Union[datetime, str]) -> ee.ImageCollection:

    # Convert dates to strings for Earth Engine if they are datetime objects
    # TODO: check that timerange is not outside of allowed range for HARMONIZED collection
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')\
        .filterDate(start_date_str, end_date_str)\
        .filterBounds(aoi)\

    return collection
