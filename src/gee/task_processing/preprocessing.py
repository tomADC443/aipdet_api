import ee
from src.gee.task_processing.constants import DAY_ONLY_FEATURE_LABEL
from src.gee.task_processing.metadata import GeeTaskProcessingMetadata


def preprocess_imagery(image_collection: ee.ImageCollection, aoi: ee.Geometry, metadata: GeeTaskProcessingMetadata) -> ee.ImageCollection:
    image_collection = remove_unused_bands(image_collection)
    image_collection = get_clipped_collection(image_collection, aoi)
    image_collection = get_mosaicked_by_day_collection(
        image_collection, metadata.time_zone)
    image_collection = mask_out_clouds_and_cloud_shadows_for_collection(
        image_collection)
    image_collection = add_metadata(image_collection, metadata)
    return image_collection


def remove_unused_bands(image_collection: ee.ImageCollection):
    return image_collection.select("SCL", "B8", "B4")


def get_clipped_collection(image_collection: ee.ImageCollection, aoi: ee.Geometry):
    return image_collection.map(lambda img: img.clip(aoi))


def get_mosaicked_by_day_collection(image_collection: ee.ImageCollection, time_zone: str):

    # Local date is needed because images are captured during the day so mosaicked by UTC date will potentially group images that are on two (local) separate days (due to timezones)
    def add_local_date(image):
        utc_time = ee.Date(image.get("system:time_start"))
        local_time = ee.Date(utc_time, time_zone)
        local_date = local_time.format("YYYY-MM-dd")  # Extract local day only
        return image.set(DAY_ONLY_FEATURE_LABEL, local_date)

    collection_with_local_date = image_collection.map(add_local_date)

    def mosaic_by_date(local_date):
        # Filter images with the same local date
        images_for_date = collection_with_local_date.filter(
            ee.Filter.eq(DAY_ONLY_FEATURE_LABEL, local_date))
        # Mosaic images
        mosaicked_image = images_for_date.mosaic().set(
            DAY_ONLY_FEATURE_LABEL, local_date)
        return mosaicked_image

    # Get unique local dates
    unique_local_dates = collection_with_local_date.aggregate_array(
        DAY_ONLY_FEATURE_LABEL).distinct()

    mosaicked_images = unique_local_dates.map(
        lambda date: mosaic_by_date(date))

    return ee.ImageCollection(mosaicked_images)


def mask_out_clouds_and_cloud_shadows_for_collection(image: ee.ImageCollection) -> ee.ImageCollection:
    return image.map(mask_out_clouds_and_cloud_shadows)


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


def add_metadata(image_collection: ee.ImageCollection, metadata) -> ee.ImageCollection:
    image_collection = image_collection.map(
        lambda image: image.set(
            "process_id", metadata.process_id,
            "user_id", metadata.user_id,
            "aoi_id", metadata.aoi_id,
            "prepared_at", metadata.prepared_at,
            "time_zone", metadata.time_zone))
    return image_collection
