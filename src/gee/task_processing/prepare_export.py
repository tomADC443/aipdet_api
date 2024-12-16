import ee


def prepare_export(image_collection: ee.ImageCollection) -> ee.FeatureCollection:

    # Flatten the ImageCollection into a FeatureCollection
    flattened_feature_collection = flatten_image_collection(image_collection)

    # Prepare the FeatureCollection for export
    prepared_feature_collection = prepare_for_export(
        flattened_feature_collection)
    return prepared_feature_collection


def extract_combined_polygons(image):
    combined_polygons = ee.FeatureCollection(image.get('combined_polygons'))
    return combined_polygons.map(
        lambda feature: feature.set('image_id', image.get('system:id'))
    )

# Flatten the ImageCollection into a FeatureCollection


def flatten_image_collection(image_collection):
    combined_polygons_fc = image_collection.map(extract_combined_polygons)
    return ee.FeatureCollection(combined_polygons_fc.flatten())

# Prepare FeatureCollection for export


def prepare_for_export(feature_collection):
    return feature_collection.select(['geometry', 'ndvi_polygons', 'image_id'])

# Export FeatureCollection to BigQuery or Drive


def export_feature_collection(feature_collection, export_type, destination, description):
    if export_type == 'bigquery':
        ee.batch.Export.table.toBigQuery(
            collection=feature_collection,
            dataset=destination['dataset'],
            tableName=destination['table_name'],
            project=destination['project_id'],
            description=description,
            selectors=['geometry', 'ndvi_polygons', 'image_id']
        ).start()
    elif export_type == 'drive':
        ee.batch.Export.table.toDrive(
            collection=feature_collection,
            description=description,
            fileFormat='GeoJSON'
        ).start()
    print(
        f"Export started to {export_type}. Monitor progress in the Earth Engine Task Manager.")
