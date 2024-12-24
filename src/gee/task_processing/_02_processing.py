import ee
from src.gee.task_processing.constants import P


def process_collection(image_collection: ee.ImageCollection,  aoi: ee.Geometry) -> ee.FeatureCollection:

    def value_derivation(image: ee.Image) -> ee.FeatureCollection:

        valid_polygon_feature_collection = image.mask().gt(0).reduceToVectors(
            geometry=aoi,
            geometryType='polygon',
            reducer=ee.Reducer.count(),
            scale=10,
            bestEffort=False,
            labelProperty=None,
            eightConnected=False,
        )
        valid_polygon_feature_collection = valid_polygon_feature_collection.map(
            lambda feature: feature.set('image_id', image.id())
        )
        return valid_polygon_feature_collection

    feature_collection = image_collection.map(value_derivation).flatten()
    return feature_collection
