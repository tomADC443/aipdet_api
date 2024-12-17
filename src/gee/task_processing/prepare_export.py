import ee
from src.gee.task_processing.constants import DAY_ONLY_FEATURE_LABEL


def prepare_export(image_collection: ee.ImageCollection) -> ee.FeatureCollection:
    # Flatten the ImageCollection into a FeatureCollection
    flattened_feature_collection = flatten_image_collection(image_collection)

    # Prepare the FeatureCollection for export
    prepared_feature_collection = prepare_for_export(
        flattened_feature_collection)
    return prepared_feature_collection


def flatten_image_collection(image_collection):
    combined_polygons_fc = image_collection.map(add_data_to_feature)
    return ee.FeatureCollection(combined_polygons_fc.flatten())


def add_data_to_feature(image):
    combined_polygons = ee.FeatureCollection(image.get('combined_polygons'))
    # Convert ndvi_polygons to MultiPolygon and set it as a property
    updated_combined_polygons = combined_polygons.map(
        lambda feature: feature.set("process_id", image.get('process_id'))
        .set("user_id", image.get('user_id'))
        .set("aoi_id", image.get('aoi_id'))
        .set("prepared_at", ee.Date(image.get('prepared_at')))
        .set("time_zone", image.get('time_zone'))
        .set('image_id', image.get('system:id'))
        # .set('utc_capture_start', ee.Date(image.get('system:time_start')))
        # .set('utc_capture_end', ee.Date(image.get('system:time_end')))
        .set(DAY_ONLY_FEATURE_LABEL, image.get(DAY_ONLY_FEATURE_LABEL))
        .set('ndvi_polygons', ee.Geometry.MultiPolygon(
            ee.FeatureCollection(feature.get(
                'ndvi_polygons')).geometry().geometries()))
    )

    return updated_combined_polygons


def prepare_for_export(feature_collection):
    return feature_collection.select(['geometry', 'ndvi_polygons', 'image_id'])
