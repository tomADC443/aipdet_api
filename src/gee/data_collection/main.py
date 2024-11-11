import ee
from src.gee.auth import authenticate
from datetime import datetime

from src.gee.data_collection.scene_collection import get_imagery

# CONFIG ======================================================================
authenticate()
AOI: ee.Geometry = ee.Geometry.Polygon([
    [
        [27.856558555543103, -25.735971295389234],
        [27.85009003133095, -25.746253573391016],
        [27.868734601118888, -25.76105849041417],
        [27.875355325900756, -25.742552055804197],
        [27.856558555543103, -25.735971295389234]
    ]
])

START_DATE: datetime = datetime(2017, 4, 1)
END_DATE: datetime = datetime(2024, 12, 31)

# =============================================================================


s2_collection = get_imagery(AOI, START_DATE, END_DATE)


print("Number of images found:", s2_collection.size().getInfo())
