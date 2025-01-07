import ee
from src.gee.task_processing.constants import DAY_ONLY_FEATURE_LABEL
from src.gee.task_processing.constants import P
from typing import Any


def start_export(feature_collection: ee.FeatureCollection, metadata) -> Any:

    task = ee.batch.Export.table.toBigQuery(
        collection=feature_collection,
        table='aiap-436610.comp_gee_data.task_process_result_v2',
        description=metadata.task_id,
        append=True,
        selectors=[
            '.geo', "image_id", "ndvi_polygons", "user_id", P['process_id'], P['water_hyacinth_classification']]
    )
    task.start()
    return task
