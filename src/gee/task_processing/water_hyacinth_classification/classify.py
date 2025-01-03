import ee


def classify_water_hyacinth_image(image: ee.Image, area: ee.Geometry,  trained_classifier: ee.Classifier) -> ee.Image:

    image = image.clip(area)

    classification_probabilities = image.classify(trained_classifier)

    higher_confidence_classification = ee.Image(0).where(
        classification_probabilities.gt(0.75), 1).clip(area)

    return higher_confidence_classification
