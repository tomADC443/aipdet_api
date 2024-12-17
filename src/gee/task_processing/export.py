import ee
from src.gee.task_processing.constants import DAY_ONLY_FEATURE_LABEL


def start_export(feature_collection: ee.FeatureCollection) -> None:

    feature_collection = feature_collection.map(
        lambda feature: feature.set(
            'user_id', ee.String(feature_collection.size())).set(
                "ndvi_polygons", feature.get('ndvi_polygons')))

    task = ee.batch.Export.table.toBigQuery(
        collection=feature_collection,
        table='aiap-436610.comp_gee_data.task_process_result_01',
        description='Pipeline_version_24',
        append=True,
        selectors=[
            "user_id", "ndvi_polygons"],
    )

    # task = ee.batch.Export.table.toBigQuery(
    #     collection=feature_collection,
    #     table='aiap-436610.comp_gee_data.task_process_result_01',
    #     description='Pipeline_version_24',
    #     append=True,
    #     selectors=[
    #         "geo",
    #         "process_id",
    #         "user_id",
    #         "aoi_id",
    #         "prepared_at",
    #         "time_zone",
    #         "image_id",
    #         "utc_capture_start",
    #         "utc_capture_end",
    #         # "ndvi_polygons",
    #         DAY_ONLY_FEATURE_LABEL
    #     ],
    # )
    task.start()
