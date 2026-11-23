import numpy as np
import pandas as pd
from config.kinetic_static_friction import get_friction


def clean_csv(path: str, hazard_type: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(path)

    # 1. Filter non-road infrastructure and pedestrian/cycleways
    dropcols = ["waterway", "aerialway", "barrier", "man_made", "railway"]
    # Drop only columns that actually exist in the CSV to avoid KeyError
    existing_dropcols = [col for col in dropcols if col in df.columns]
    df = df.drop(columns=existing_dropcols)

    drop_surfaces = [
        "path",
        "footway",
        "pedestrian",
        "steps",
        "proposed",
        "cycleway",
        "elevator",
        "track",
        "platform",
        "rest_area",
    ]
    df = df[~df["highway"].isin(drop_surfaces)].copy()

    # 2. Extract tags stored in other_tags
    if "other_tags" in df.columns:
        df["maxspeed"] = df["other_tags"].str.extract(r'"maxspeed"=>"([^"]+)"')
        df["surface"] = df["other_tags"].str.extract(r'"surface"=>"([^"]+)"')
    else:
        if "maxspeed" not in df.columns:
            df["maxspeed"] = np.nan
        if "surface" not in df.columns:
            df["surface"] = np.nan

    df["maxspeed"] = pd.to_numeric(df["maxspeed"], errors="coerce")

    # 3. Dynamic speed fallback based on hazard condition
    if hazard_type == "snow":
        fallback_speed = 20.0
    else:
        is_residential = df["highway"].astype(str).str.lower().eq("residential")
        fallback_speed = np.where(is_residential, 30.0, 50.0)

    # Fill missing maxspeeds with conditional fallback
    df["maxspeed"] = df["maxspeed"].fillna(pd.Series(fallback_speed, index=df.index))

    # 4. Map friction coefficients from lookup module
    df["friction"] = df["surface"].apply(get_friction)
    df["mu_static"] = df["friction"].apply(
        lambda x: x[0] if isinstance(x, (tuple, list)) else np.nan
    )
    df["mu_kinetic"] = df["friction"].apply(
        lambda x: x[1] if isinstance(x, (tuple, list)) else np.nan
    )

    # Clean intermediate tuple column
    df = df.drop(columns=["friction"])

    return df
