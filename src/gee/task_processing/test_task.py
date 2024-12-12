import ee
from src.gee.auth import authenticate

# Initialize the Earth Engine API


def test_task():

    authenticate()

    # Define the area of interest (example: a rectangle)

    # Define the area of interest (example: a rectangle)
    roi = ee.Geometry.Rectangle([27.85, -25.74, 27.88, -25.70])

    # Select one image from the Sentinel-2 Harmonized collection
    image_collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(roi) \
        .filterDate('2024-01-01', '2024-01-31') \
        .sort('CLOUD_COVER')

    selected_image = ee.Image(image_collection.first())

    # Calculate NDVI
    ndvi = selected_image.normalizedDifference(['B8', 'B4']).rename('NDVI')

    # Get mean NDVI for the area of interest
    ndvi_mean = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=10
    )

    # Create FeatureCollection without system:index
    results = ee.FeatureCollection([
        ee.Feature(roi, {'NDVI_Mean': ndvi_mean.get('NDVI')})
    ]).map(lambda feature: feature.set({'system:index': None}))

    # Export the result to a BigQuery table
    task = ee.batch.Export.table.toBigQuery(
        collection=results,
        # Replace with your BigQuery dataset name
        table='aiap-436610.comp_gee_data.test',
        description='Export_NDVI_Mean',
        append=True,  # Append results to the table
        selectors=["NDVI_Mean", "geo"],  # Select the NDVI_Mean property
    )

    # Start the task
    task.start()

    # Monitor the task
    print('Export started. Check the Earth Engine Task Manager for progress.')
