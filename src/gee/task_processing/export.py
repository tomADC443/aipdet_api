import ee


def create_export_task(feature_collection: ee.FeatureCollection) -> ee.batch.Export.table.toBigQuery:

    task = ee.batch.Export.table.toBigQuery(
        collection=feature_collection,
        # Replace with your BigQuery dataset name
        table='aiap-436610.comp_gee_data.test',
        description='Export_NDVI_Mean',
        append=True,  # Append results to the table
        selectors=["NDVI_Mean", "geo"],  # Select the NDVI_Mean property
    )

    # Start the task
    task.start()
