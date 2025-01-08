import ee
from src.gee.task_processing.constants import DAY_ONLY_FEATURE_LABEL
from src.gee.task_processing.constants import P
from src.gee.task_processing.metadata import GeeTaskProcessingMetadata


def prepare_export(featureCollection: ee.FeatureCollection, metadata: GeeTaskProcessingMetadata, image: ee.Image) -> ee.FeatureCollection:

    featureCollection = featureCollection.map(
        lambda feature: feature.set(P["process_id"], metadata.task_id)
        .set(P["utc_capture_start"], image.get("system:time_start"))
        .set(P["user_id"], metadata.user_id)
    )
    return featureCollection
