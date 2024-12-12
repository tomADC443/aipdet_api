import ee


def process_collection(image_collection: ee.ImageCollection):

    image_collection = image_collection.map(add_ndvi)
    image_collection = image_collection.map(generate_valid_area_polygons)
    image_collection = image_collection.map(generate_ndvi_polygons)
    image_collection = image_collection.map(combine_ndvi_and_valid_polygons)


def add_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)


def generate_valid_area_polygons(image: ee.Image) -> ee.Image:
    # Masked areas are considered invalid
    valid_mask = image.mask()
    valid_polygons = valid_mask.reduceToVectors(
        geometryType='polygon',
        reducer=ee.Reducer.count(),
        scale=10,
        bestEffort=True
    )
    image.set('valid_polygons', valid_polygons)
    return image


def generate_ndvi_polygons(image: ee.Image):

    ndvi_polygons = image.select('NDVI').gte(0.6).reduceToVectors(
        geometryType='polygon',
        reducer=ee.Reducer.count(),
        scale=10,
        bestEffort=True
    )
    image.set('ndvi_polygons', ndvi_polygons)
    return image


def combine_ndvi_and_valid_polygons(image: ee.Image):
    valid_polygons = image.get('valid_polygons')
    ndvi_polygons = image.get('ndvi_polygons')
    valid_polygons_feat_coll = ee.FeatureCollection(valid_polygons)
    ndvi_polygons_feat_coll = ee.FeatureCollection(ndvi_polygons)
    combined_polygons = valid_polygons_feat_coll.map(
        lambda valid_feature: valid_feature.set(
            'ndvi_polygons', ndvi_polygons_feat_coll.filterBounds(
                valid_feature.geometry())
        )
    )
    image.set('combined_polygons', combined_polygons)
    return image
