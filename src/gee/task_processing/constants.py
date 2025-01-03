
# Availability of Sentinel-2 imagery starts at 01.04.2017
NUMBER_OF_DAYS_TEMPORAL_MAX = 2  # 7 years back = 2555 days
DAY_ONLY_FEATURE_LABEL = "reduced_local_day"


# P = Property (name of a property (e.g. of an image))
# B = Band (name of a band)
# S = Settings
P = {
    "ndvi_polygons": "ndvi_polygons",
    "image_id": "image_id",
    "process_id": "process_id",
    "water_hyacinth_classification": "water_hyacinth_classification",
}

B = {
    "NDVI": "NDVI",
    "NDVI_GT_07": "NDVI_GT_07"
}


S = {
    "HIGH_NDVI_THRESHOLD": 0.7,
    "BASIC_SIMPLIFY_TOLERANCE": 20,
    "TOLERANCE_UNIT": "meters",
    "SENTINEL2_SCALE": 10,

}
