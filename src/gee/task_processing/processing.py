import ee
from src.gee.task_processing.constants import P


def process_collection(image_collection: ee.ImageCollection, aoi: ee.Geometry) -> ee.ImageCollection:

    image_collection = add_ndvi(image_collection, aoi)
    image_collection = generate_valid_area_polygons(image_collection, aoi)
    image_collection = generate_ndvi_polygons(image_collection, aoi)
    image_collection = image_collection.map(combine_ndvi_and_valid_polygons)
    return image_collection


def add_ndvi(image_collection: ee.ImageCollection, aoi: ee.Geometry) -> ee.ImageCollection:

    def add_ndvi(image):
        return image.clip(aoi).addBands(image.clip(aoi).normalizedDifference(['B8', 'B4']).rename('NDVI'))
    return image_collection.map(add_ndvi)


def generate_valid_area_polygons(image_collection: ee.ImageCollection, aoi: ee.Geometry) -> ee.ImageCollection:

    def valid_areas_to_polygons(image):
        return image.select("B4").mask().gt(0).selfMask().toInt().reduceToVectors(
            geometry=aoi,
            geometryType='polygon',
            reducer=ee.Reducer.countEvery(),
            scale=10,
            bestEffort=True,
            labelProperty=None,
            eightConnected=False,
        )

    def set_polygons(image):
        return image.set('valid_polygons', valid_areas_to_polygons(image))

    image_collection = image_collection.map(set_polygons)

    return image_collection


def generate_ndvi_polygons(image_collection: ee.ImageCollection, aoi: ee.Geometry) -> ee.ImageCollection:

    def add_high_ndvi_band(image: ee.Image) -> ee.Image:
        return image.addBands(image.select("NDVI").gt(0.7).rename("NDVI_GT_07"))

    def add_utility_band(image: ee.Image) -> ee.Image:
        return image.select("NDVI_GT_07").addBands(image.select("NDVI").rename("temp_band"))

    def add_connected_areas_as_band(image: ee.Image) -> ee.Image:
        return image.addBands(image.reduceConnectedComponents(  # "temp_band" is used here as the dummy band for the reducer)
            reducer=ee.Reducer.allNonZero(),
            labelBand='NDVI_GT_07',
            maxSize=1000000
        ).rename('NDVI_GT_07_connected_components'))

    def add_high_ndvi_feature_collection(image: ee.Image) -> ee.Image:

        def ndvi_areas_to_polygons(image: ee.Image) -> ee.Geometry:
            vectors = image.select('NDVI_GT_07_connected_components').reduceToVectors(
                geometry=aoi,
                geometryType='polygon',
                reducer=ee.Reducer.countEvery(),
                scale=10,
                bestEffort=False,
                labelProperty=None,
                eightConnected=False,
            )

            simplified_vectors = vectors.map(
                lambda feature: feature.simplify(
                    ee.ErrorMargin(1, 'meters'))  # 1 meter simplification
            )

            simplified_vectors = ee.FeatureCollection(simplified_vectors)

            return ee.Geometry.MultiPolygon(
                simplified_vectors.geometry().geometries()
            )

        return ee.Image(image.set(P['ndvi_multipolygons'], ndvi_areas_to_polygons(image)))

    image_collection = image_collection.map(add_high_ndvi_band)
    image_collection = image_collection.map(add_utility_band)
    image_collection = image_collection.map(add_connected_areas_as_band)
    image_collection = image_collection.map(add_high_ndvi_feature_collection)
    return image_collection


def combine_ndvi_and_valid_polygons(image: ee.Image) -> ee.Image:
    valid_polygons = image.get('valid_polygons')
    ndvi_polygons = image.get(P['ndvi_multipolygons'])
    valid_polygons_feat_coll = ee.FeatureCollection(valid_polygons)
    ndvi_polygons_feat_coll = ee.FeatureCollection(ndvi_polygons)
    combined_polygons = ee.FeatureCollection(valid_polygons_feat_coll.map(
        lambda valid_feature: valid_feature.set(
            P['ndvi_multipolygons'], ndvi_polygons_feat_coll.filter(
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
    return ee.Image(image.set(P['combined_polygons'], combined_polygons))
