import ee


def get_defective_pixel_vector_mask_from_SCL(image: ee.Image, aoi: ee.Geometry.Polygon) -> ee.Feature:

    clipped_image = image.clip(aoi)
    scl = clipped_image.select('SCL')
    defective_mask = scl.eq(1)
    defective_areas = defective_mask.mask(defective_mask).reduceToVectors(
        geometryType='polygon',
        reducer=ee.Reducer.countEvery(),
        scale=10,  # Adjust based on Sentinel-2 resolution (10m)
        maxPixels=1e8
    )
    return defective_areas
