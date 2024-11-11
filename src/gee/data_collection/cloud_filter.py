import ee


def get_could_vector_mask(image: ee.Image, aoi: ee.Geometry.Polygon) -> ee.Feature:

    clipped_image = image.clip(aoi)
    scl = clipped_image.select('SCL')
    could_mask = scl.eq(3)
    could_areas = could_mask.mask(could_mask).reduceToVectors(
        geometryType='polygon',
        reducer=ee.Reducer.countEvery(),
        scale=10,  # Adjust based on Sentinel-2 resolution (10m)
        maxPixels=1e8
    )
    return could_areas


def get_could_shadow_vector_mask(image: ee.Image, aoi: ee.Geometry.Polygon) -> ee.Feature:

    clipped_image = image.clip(aoi)
    scl = clipped_image.select('SCL')
    could_mask = scl.eq(3)
    could_areas = could_mask.mask(could_mask).reduceToVectors(
        geometryType='polygon',
        reducer=ee.Reducer.countEvery(),
        scale=10,  # Adjust based on Sentinel-2 resolution (10m)
        maxPixels=1e8
    )
    return could_areas
