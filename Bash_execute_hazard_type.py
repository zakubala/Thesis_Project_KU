import os
import subprocess
import geopandas as gpd
import rasterio
from Scalgo_bbox import get_raster_bbox_wgs84
from cleaning_streets import clean_streets_gdf
import numpy as np


def hazard_choice(hazard_type: str):
    if hazard_type == "flood":
        scalgo_raster_path = (
            "Scalgo Data/Terrain_Buildings_Wrocław_Water_depth_Rain=7_24_m.tif"
        )
        output_vector_path = "Output files cached/wroclaw_streets.gpkg"

        if not os.path.exists(output_vector_path):
            min_lon, min_lat, max_lon, max_lat = get_raster_bbox_wgs84(
                scalgo_raster_path
            )
            subprocess.run(
                [
                    "bash",
                    "Bash Scripts/wroclaw_streets_bash.sh",
                    str(min_lon),
                    str(min_lat),
                    str(max_lon),
                    str(max_lat),
                ],
                check=True,
            )

        gdf_edges = gpd.read_file(output_vector_path, layer="streets")
        gdf_edges = clean_streets_gdf(gdf_edges, hazard_type="flood")

        with rasterio.open(scalgo_raster_path) as src:
            edges_native = gdf_edges.to_crs(src.crs)
            coords = [
                (geom.centroid.x, geom.centroid.y) for geom in edges_native.geometry
            ]
            raw_depths = [val[0] for val in src.sample(coords)]
            nodata_val = src.nodata if src.nodata is not None else -9999.0

            gdf_edges["water_depth_m"] = [
                (
                    0.0
                    if (np.isclose(v, nodata_val, atol=1e4) or v < 0.0 or np.isnan(v))
                    else float(v)
                )
                for v in raw_depths
            ]

            # change to metric UTM for A* routing, not lat/lon
            edges_utm = gdf_edges.to_crs("EPSG:32633")

        return edges_utm, scalgo_raster_path

    elif hazard_type == "snow":
        scalgo_raster_path = "not applicable for snow hazards - assume snow collects uniformly on all roads"
        output_vector_path = "Output files cached/syracuse_streets.gpkg"

        if not os.path.exists(output_vector_path):
            # min_lon, min_lat, max_lon, max_lat
            syracuse_bbox = ["-76.49", "42.77", "-75.89", "43.27"]
            subprocess.run(
                ["bash", "Bash Scripts/syracuse_streets_bash.sh", *syracuse_bbox],
                check=True,
            )

        gdf_edges = gpd.read_file(output_vector_path, layer="streets")
        gdf_edges = clean_streets_gdf(gdf_edges, hazard_type="snow")

        # change to metric UTM for A* routing, not lat/lon
        edges_utm = gdf_edges.to_crs("EPSG:32633")
        return edges_utm, scalgo_raster_path

    else:
        raise ValueError("Invalid hazard type. Choose 'flood' or 'snow'.")
