import ee
from src.processing_pipeline.gee.water_hyacinth_classification.train import train_classifier
from src.processing_pipeline.gee.water_hyacinth_classification.classify import classify_water_hyacinth_image
from src.processing_pipeline.gee.task_processing.constants import P, S


def classify_water_hyacinth(image: ee.Image, valid_polygon_feature_collection: ee.FeatureCollection) -> ee.FeatureCollection:

    classifier = ee.Classifier.smileRandomForest(
        numberOfTrees=100).setOutputMode('PROBABILITY')

    trained_classifier = train_classifier(classifier)

    def classify_feature(valid_polygon_feature: ee.Feature) -> ee.Feature:

        classified_image = classify_water_hyacinth_image(
            image, valid_polygon_feature.geometry(), trained_classifier)

        classified_water_hyacinth_collection = classified_image.selfMask().reduceToVectors(
            geometry=valid_polygon_feature.geometry(),
            geometryType='polygon',
            reducer=ee.Reducer.countEvery(),
            scale=S["SENTINEL2_SCALE"],  # type: ignore
            bestEffort=False,
            labelProperty=None,
            eightConnected=True,
        )

        simplified_vectors = classified_water_hyacinth_collection.map(
            lambda feature: feature.buffer(5).simplify(ee.ErrorMargin(
                # type: ignore

                6, S["TOLERANCE_UNIT"]))  # type: ignore
            .buffer(-4).simplify(ee.ErrorMargin(
                15, S["TOLERANCE_UNIT"])).dissolve()  # type: ignore
        )

        def enforce_polygon(feature: ee.Feature) -> ee.Feature:
            geom = feature.geometry()
            polygon = geom.buffer(1).simplify(1)

            return feature.setGeometry(polygon)
        simplified_vectors = simplified_vectors.map(enforce_polygon)

        # cleaned_collection = simplified_vectors.map(
        #     lambda feature: feature.setGeometry(
        #         feature.geometry().transform('EPSG:4326',
        #                                      ee.ErrorMargin(
        #                                          S["BASIC_SIMPLIFY_TOLERANCE"], S["TOLERANCE_UNIT"])  # type: ignore
        #                                      )
        #     )
        # )

        has_features = simplified_vectors.size().gt(0)

        feature = ee.Feature(ee.Algorithms.If(
            has_features,
            valid_polygon_feature.set(
                P['water_hyacinth_classification'], simplified_vectors.geometry()),
            valid_polygon_feature)
        )
        return feature

    return valid_polygon_feature_collection.map(classify_feature)
