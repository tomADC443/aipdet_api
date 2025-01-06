import ee
# P= Property B= Band S= Settings
from src.gee.task_processing.constants import P, B, S
from src.gee.task_processing.utils import calculate_masked_percentage
from src.gee.task_processing.water_hyacinth_classification.main import classify_water_hyacinth


def image_to_vector_polygons(image: ee.Image, aoi: ee.Geometry, reducer: ee.Reducer) -> ee.FeatureCollection:
    vector_polygons = image.reduceToVectors(
        geometry=aoi,
        geometryType='polygon',
        reducer=reducer,
        scale=S["SENTINEL2_SCALE"],  # type: ignore
        bestEffort=False,
        labelProperty=None,
        eightConnected=False,
    )
    vector_polygons = vector_polygons.map(lambda feature: feature.simplify(5))
    return vector_polygons


def process_collection(image: ee.Image,  aoi: ee.Geometry) -> ee.FeatureCollection:

    def add_bands(image: ee.Image) -> ee.Image:
        image = image.addBands(image.clip(aoi).normalizedDifference(
            ['B8', 'B4']).rename(B["NDVI"]).clip(aoi))
        image = image.addBands(image.select(
            B["NDVI"]).gt(S["HIGH_NDVI_THRESHOLD"]).rename(B["NDVI_GT_07"]))

        return image.updateMask(image.mask())

    def value_derivation(image: ee.Image) -> ee.FeatureCollection:

        valid_polygon_feature_collection = image_to_vector_polygons(
            image.mask().updateMask(image.mask()).gt(0), aoi, ee.Reducer.count())

        valid_polygon_feature_collection = valid_polygon_feature_collection.map(
            lambda feature: feature.set(P['image_id'], image.id())
        )

        def set_ndvi_area_inside_polygon(feature: ee.Feature) -> ee.Feature:

            ndvi_vectors = image_to_vector_polygons(image.select(B["NDVI_GT_07"]).mask(
                image.select(B["NDVI_GT_07"]).eq(1)), feature.geometry(), ee.Reducer.countEvery())

            has_features = ndvi_vectors.size().gt(0)

            # Set geometry only if features exist
            feature = ee.Feature(ee.Algorithms.If(
                has_features,
                feature.set(P['ndvi_polygons'], ndvi_vectors.geometry()),
                feature
            ))

            return feature

        valid_ndvi_feature_collection = valid_polygon_feature_collection.map(
            set_ndvi_area_inside_polygon)
        # valid_ndvi_classified_feature_collection = classify_water_hyacinth(
        #     image, valid_ndvi_feature_collection)
        return valid_ndvi_feature_collection

    # Add bands to the image collection
    image = add_bands(image)
    # Now Feature Collection of valid polygons with image_id
    feature_collection = value_derivation(image)

    return feature_collection
