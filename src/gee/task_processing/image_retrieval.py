import ee
from datetime import datetime, time
from typing import List, Dict
import pytz


def get_imagery(
    aoi: ee.Geometry,
    start_date: int,
    end_date: int,
) -> ee.ImageCollection:

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start_date, end_date)
        .filterBounds(aoi)
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", 95))
    )
    return collection


def get_date_ranges(
    aoi: ee.Geometry,
    start_date_ms: int,
    end_date_ms: int,
    timezone: str
) -> List[Dict]:
    collection = get_imagery(aoi, start_date_ms, end_date_ms)
    if collection.size().getInfo() == 0:
        return []

    tz = pytz.timezone(timezone)
    image_list = collection.getInfo()['features']  # type: ignore

    local_dates = {
        datetime.fromtimestamp(
            image['properties']['system:time_start']/1000,  # type: ignore
            tz=pytz.UTC
        ).astimezone(tz).date()
        for image in image_list
    }

    ranges = []
    for local_date in sorted(local_dates):
        local_start = tz.localize(datetime.combine(local_date, time.min))
        local_end = tz.localize(datetime.combine(local_date, time.max))

        utc_start = local_start.astimezone(pytz.UTC)
        utc_end = local_end.astimezone(pytz.UTC)

        ranges.append({
            'start_date': int(utc_start.timestamp() * 1000),
            'end_date': int(utc_end.timestamp() * 1000)
        })
    print(len(ranges))
    return ranges
