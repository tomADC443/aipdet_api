import ee
from src.processing_pipeline.gee.task_processing.constants import DAY_ONLY_FEATURE_LABEL
from src.processing_pipeline.gee.task_processing.constants import P
from src.processing_pipeline.gee.task_processing.metadata import GeeTaskProcessingMetadata


def prepare_export(featureCollection: ee.FeatureCollection, metadata: GeeTaskProcessingMetadata, image: ee.Image) -> ee.FeatureCollection:

    featureCollection = featureCollection.map(
        lambda feature: feature.set(P["process_id"], metadata.task_id)
        .set(P["utc_capture_start"], ee.Date(ee.Number(image.get(P["utc_capture_start"]))).format('yyyy-MM-dd'))
        .set(P["user_id"], metadata.user_id)
    )
    return featureCollection
