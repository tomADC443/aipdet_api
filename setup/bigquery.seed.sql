-- Create a bigquery instance and setup the following tables:
CREATE TABLE spatial_analysis_grid_v9 (
    process_id STRING NOT NULL,
    cell_id STRING NOT NULL,
    cell_area FLOAT64 NOT NULL,
    cell_intersection_area FLOAT64 NOT NULL,
    cell_coverage_ratio FLOAT64 NOT NULL,
    geometry GEOGRAPHY NOT NULL,
    total_observed_area FLOAT64 NOT NULL,
    total_ndvi_area FLOAT64 NOT NULL,
    ndvi_score FLOAT64 NOT NULL,
    total_whc_area FLOAT64 NOT NULL,
    whc_score FLOAT64 NOT NULL
);

CREATE TABLE task_process_result_v2 (
    geo GEOGRAPHY,
    process_id STRING,
    user_id STRING,
    aoi_id STRING,
    prepared_at DATE,
    time_zone STRING,
    image_id STRING,
    utc_capture_start DATE,
    utc_capture_end DATE,
    ndvi_polygons GEOGRAPHY,
    reduced_local_day STRING,
    ndvi_multipolygon GEOGRAPHY,
    count STRING,
    created_at DATETIME DEFAULT CURRENT_DATETIME(),
    water_hyacinth_classification GEOGRAPHY
);