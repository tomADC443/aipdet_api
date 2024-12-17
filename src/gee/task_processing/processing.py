import ee


def process_collection(image_collection: ee.ImageCollection, aoi: ee.Geometry) -> ee.ImageCollection:

    image_collection = image_collection.map(add_ndvi)
    image_collection = generate_valid_area_polygons(image_collection, aoi)
    image_collection = generate_ndvi_polygons(image_collection, aoi)
    image_collection = image_collection.map(combine_ndvi_and_valid_polygons)

    return image_collection


def add_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)


def generate_valid_area_polygons(image_collection: ee.ImageCollection, aoi: ee.Geometry) -> ee.ImageCollection:

    def valid_areas_to_polygons(image):
        return image.select("B4").mask().gt(0).selfMask().toInt().reduceToVectors(
            geometry=aoi,
            geometryType='polygon',
            reducer=ee.Reducer.countEvery(),
            scale=10,
            bestEffort=True
        )

    def set_polygons(image):
        return image.set('valid_polygons', valid_areas_to_polygons(image))

    image_collection = image_collection.map(set_polygons)
    return image_collection


def generate_ndvi_polygons(image_collection: ee.ImageCollection, aoi: ee.Geometry) -> ee.ImageCollection:

    def ndvi_areas_to_polygons(image):
        vectors = image.select('NDVI').gte(0.6).reduceToVectors(
            geometryType='polygon',
            geometry=aoi,
            reducer=ee.Reducer.countEvery(),
            scale=10,
            bestEffort=True
        )

        simplified_vectors = vectors.map(
            lambda feature: feature.simplify(
                ee.ErrorMargin(100, 'meters'))  # 1 meter simplification
        )
        return simplified_vectors

    def set_polygons(image):
        return image.set('ndvi_polygons', ndvi_areas_to_polygons(image))

    image_collection = image_collection.map(set_polygons)

    return image_collection


def combine_ndvi_and_valid_polygons(image: ee.Image) -> ee.Image:
    valid_polygons = image.get('valid_polygons')
    ndvi_polygons = image.get('ndvi_polygons')
    valid_polygons_feat_coll = ee.FeatureCollection(valid_polygons)
    ndvi_polygons_feat_coll = ee.FeatureCollection(ndvi_polygons)
    combined_polygons = ee.FeatureCollection(valid_polygons_feat_coll.map(
        lambda valid_feature: valid_feature.set(
            'ndvi_polygons', ndvi_polygons_feat_coll.filter(
                ee.Filter.Or(
                    # Fully inside
                    ee.Filter.contains('.geo', valid_feature.geometry()),
                    # Exactly equal
                    ee.Filter.equals('.geo', valid_feature.geometry())
                )
            )
        )
    )
    )
    return ee.Image(image.set('combined_polygons', combined_polygons))


def clean_geometry(feature):
    # 1 meter error Tollerance
    return feature.setGeometry(feature.geometry().simplify(ee.ErrorMargin(1, 'meters')))
