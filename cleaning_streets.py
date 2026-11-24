import numpy as np
import pandas as pd
import geopandas as gpd
from config.kinetic_static_friction import get_friction


def clean_streets_gdf(
    gdf: gpd.GeoDataFrame, hazard_type: str | None = None
) -> gpd.GeoDataFrame:
    # 1. Drop non-road columns if present
    dropcols = ["waterway", "aerialway", "barrier", "man_made", "railway"]
    existing_dropcols = [col for col in dropcols if col in gdf.columns]
    gdf = gdf.drop(columns=existing_dropcols)

    # 3. Extract tags from other_tags (GDAL hstore format)
    if "other_tags" in gdf.columns:
        gdf["maxspeed"] = gdf["other_tags"].str.extract(r'"maxspeed"=>"([^"]+)"')
        gdf["surface"] = gdf["other_tags"].str.extract(r'"surface"=>"([^"]+)"')
    else:
        gdf["maxspeed"] = gdf.get("maxspeed", np.nan)
        gdf["surface"] = gdf.get("surface", np.nan)

    # Extract numeric part even if units like "30 mph" are present
    gdf["maxspeed"] = pd.to_numeric(
        gdf["maxspeed"].astype(str).str.extract(r"(\d+(?:\.\d+)?)")[0],
        errors="coerce",
    )

    # 4. Dynamic speed fallback
    if hazard_type == "snow":
        fallback_speed = 20.0
    else:
        is_residential = gdf["highway"].astype(str).str.lower().eq("residential")
        fallback_speed = np.where(is_residential, 30.0, 50.0)

    gdf["maxspeed"] = gdf["maxspeed"].fillna(pd.Series(fallback_speed, index=gdf.index))

    # 5. Map static and kinetic friction coefficients
    friction = gdf["surface"].apply(get_friction)
    gdf["mu_static"] = friction.apply(
        lambda x: x[0] if isinstance(x, (tuple, list)) else np.nan
    )
    gdf["mu_kinetic"] = friction.apply(
        lambda x: x[1] if isinstance(x, (tuple, list)) else np.nan
    )

    return gdf
