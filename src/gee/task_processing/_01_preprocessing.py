import ee
from src.gee.task_processing.constants import DAY_ONLY_FEATURE_LABEL
from src.gee.task_processing.metadata import GeeTaskProcessingMetadata


def preprocess_imagery(image_collection: ee.ImageCollection, aoi: ee.Geometry, metadata: GeeTaskProcessingMetadata) -> ee.Image:

    # Add intersection percentage
    # def add_intersection(image):
    #     intersection = image.geometry().intersection(aoi, 1)
    #     return image.set('intersection_area', intersection.area())

    # image_collection = image_collection.map(add_intersection)

    # # Filter out images with minimal intersection
    # image_collection = image_collection.filter(
    #     ee.Filter.gt('intersection_area', 0))

    def remove_unused_bands(image_collection: ee.ImageCollection):
        return image_collection.select("SCL", "B8", "B4")

    def get_clipped_collection(image_collection: ee.ImageCollection, aoi: ee.Geometry):
        return image_collection.map(lambda img: img.clip(aoi))

    # image_collection = remove_unused_bands(image_collection)
    # image_collection = get_clipped_collection(image_collection, aoi)

    image = image_collection.mosaic()

    image = mask_out_clouds_and_cloud_shadows(image_collection.first())

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
