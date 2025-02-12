import ee
from src.processing_pipeline.gee.task_processing.metadata import GeeTaskProcessingMetadata
from src.processing_pipeline.gee.task_processing.constants import P


def preprocess_imagery(image_collection: ee.ImageCollection, aoi: ee.Geometry, metadata: GeeTaskProcessingMetadata) -> ee.Image:

    def remove_unused_bands(image_collection: ee.ImageCollection):
        return image_collection.select("SCL", "B8", "B4")

    def get_clipped_collection(image_collection: ee.ImageCollection, aoi: ee.Geometry):
        return image_collection.map(lambda img: img.clip(aoi))

    image = image_collection.mosaic()

    image = mask_out_clouds_and_cloud_shadows(image_collection.first())
    capture_date = image_collection.first().get('system:time_start')
    image = image.set(P["utc_capture_start"], capture_date)
    return image


def mask_out_clouds_and_cloud_shadows(image: ee.Image) -> ee.Image:
    """Masks out clouds and cloud shadows for each image in the collection. The mask is created using the SCL band."""

    def get_cloud_vector_mask(image: ee.Image) -> ee.Image:
        scl = image.select("SCL")
        # Classes 10, 9, and 8  correspond to (cloud, cirrus, and high probability cloud)
        cloud_mask = scl.eq(10).Or(scl.eq(9)).Or(scl.eq(8))
        return cloud_mask

    def get_cloud_shadow_vector_mask(image: ee.Image) -> ee.Image:
        scl = image.select("SCL")
        # Class 3 is cloud shadow
        cloud_shadow_mask = scl.eq(3)
        return cloud_shadow_mask

    cloud_mask = get_cloud_vector_mask(image)
    cloud_shadow_mask = get_cloud_shadow_vector_mask(image)

    combined_mask = cloud_mask.Or(cloud_shadow_mask)

    # combine masks and mask out clouds and shadows
    return image.updateMask(combined_mask.Not())
