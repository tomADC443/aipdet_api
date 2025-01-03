import ee
from src.gee.task_processing.water_hyacinth_classification.statics import train_image_resource_id, bands, get_train_roi, get_other_class_data, get_water_hyacinth_data


def train_classifier(classifier: ee.Classifier):

    train_roi = get_train_roi()
    waterHyacinth = get_water_hyacinth_data()
    other = get_other_class_data()

    training_image = ee.Image(train_image_resource_id).clip(train_roi)

    training_image = training_image.select(bands)

    trainingData = training_image.sampleRegions(
        collection=ee.FeatureCollection([
            ee.Feature(other, {'class': 0, 'label': 'other'}),
            ee.Feature(waterHyacinth, {'class': 1, 'label': 'waterHyacinth'})
        ]),
        properties=['class'],
        scale=10
    )

    trained_classifier = classifier.train(
        features=trainingData,
        classProperty='class',
        inputProperties=bands
    )
    return trained_classifier
