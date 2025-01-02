import ee
from src.gee.task_processing.constants import P
from src.gee.task_processing.utils import calculate_masked_percentage


def process_collection(image_collection: ee.ImageCollection,  aoi: ee.Geometry) -> ee.FeatureCollection:

    def add_bands(image: ee.Image) -> ee.Image:
        image = image.addBands(image.clip(aoi).normalizedDifference(
            ['B8', 'B4']).rename('NDVI').clip(aoi))
        image = image.addBands(image.select(
            "NDVI").gt(0.7).rename("NDVI_GT_07"))

        return image.updateMask(image.mask())

    def value_derivation(image: ee.Image) -> ee.FeatureCollection:

        valid_polygon_feature_collection = image.mask().unmask(0).gt(0).reduceToVectors(
            geometry=aoi,
            geometryType='polygon',
            reducer=ee.Reducer.count(),
            scale=10,
            bestEffort=False,
            labelProperty=None,
            eightConnected=False,
        )

        valid_polygon_feature_collection = valid_polygon_feature_collection.map(
            lambda feature: feature.simplify(ee.ErrorMargin(20, 'meters'))
        )
        # mask_percent = calculate_masked_percentage(image, aoi)
        # valid_polygon_feature_collection = valid_polygon_feature_collection.map(
        #     lambda feature: feature.set('user_id', mask_percent)
        # )

        valid_polygon_feature_collection = valid_polygon_feature_collection.map(
            lambda feature: feature.set('image_id', image.id())
        )

        def set_ndvi_area_inside_polygon(feature: ee.Feature) -> ee.Feature:

            ndvi_vectors = image.select('NDVI_GT_07').eq(1).reduceToVectors(
                geometry=feature.geometry(),
                geometryType='polygon',
                reducer=ee.Reducer.countEvery(),
                scale=10,
                bestEffort=False,
                labelProperty=None,
                eightConnected=False,
            )
            ndvi_vectors = ndvi_vectors.map(
                lambda feature: feature.simplify(ee.ErrorMargin(20, 'meters'))
            )

            # Check if collection has features
            has_features = ndvi_vectors.size().gt(0)

            # Set geometry only if features exist
            feature = ee.Feature(ee.Algorithms.If(
                has_features,
                feature.set('ndvi_polygons', ndvi_vectors.geometry()),
                feature
            ))

            return feature

        return valid_polygon_feature_collection.map(set_ndvi_area_inside_polygon)

    # Add bands to the image collection
    image_collection = image_collection.map(add_bands)
    # Now Feature Collection of valid polygons with image_id
    feature_collection = image_collection.map(value_derivation).flatten()

    return feature_collection
