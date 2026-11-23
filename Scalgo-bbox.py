import rasterio
from rasterio.warp import transform_bounds


def get_raster_bbox_wgs84(raster_path):
    """
    Get the bounding box of a raster in WGS84 coordinates.

    Parameters:
    raster_path (str): Path to the raster file.

    Returns:
    tuple: (min_lon, min_lat, max_lon, max_lat) in WGS84 coordinates.
    """
    with rasterio.open(raster_path) as src:
        native_bounds = src.bounds
        raster_crs = src.crs

        # Transform native bounds to WGS84 (EPSG:4326)
        min_lon, min_lat, max_lon, max_lat = transform_bounds(
            raster_crs,
            "EPSG:4326",
            native_bounds.left,
            native_bounds.bottom,
            native_bounds.right,
            native_bounds.top,
        )

    return min_lon, min_lat, max_lon, max_lat
