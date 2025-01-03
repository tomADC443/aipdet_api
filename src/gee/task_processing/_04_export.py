import ee
from src.gee.task_processing.constants import DAY_ONLY_FEATURE_LABEL
from src.gee.task_processing.constants import P


def start_export(feature_collection: ee.FeatureCollection) -> None:

    task = ee.batch.Export.table.toBigQuery(
        collection=feature_collection,
        table='aiap-436610.comp_gee_data.task_process_result_v2',
        description='Pipeline_version_67',
        append=True,
        selectors=[
            '.geo', "image_id", "ndvi_polygons", "user_id", P["water_hyacinth_classification"], P['process_id']]
    )
    task.start()
