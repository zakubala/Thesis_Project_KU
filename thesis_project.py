# %% 1. Import Libraries
import math
import numpy as np
import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import rasterio
import os
from rasterio.windows import from_bounds
from rasterio.plot import plotting_extent
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
import subprocess

gdf_edges = gpd.read_file("Data/wroclaw_streets.gpkg", layer="streets")
print(f"Loaded {len(gdf_edges)} street segments.")
print(gdf_edges[["highway", "name", "geometry"]].head())

# %% 3. Sample Water Depth in Native Raster CRS
with rasterio.open(scalgo_raster_path) as src:
    edges_native = gdf_edges.to_crs(src.crs)
    coords = [(geom.centroid.x, geom.centroid.y) for geom in edges_native.geometry]
    raw_depths = [val[0] for val in src.sample(coords)]

    gdf_edges["water_depth_m"] = [
        (
            0.0
            if (np.isclose(v, nodata_val, atol=1e4) or v < 0.0 or np.isnan(v))
            else float(v)
        )
        for v in raw_depths
    ]

# Project to metric UTM for A* routing
edges_utm = gdf_edges.to_crs("EPSG:32632")

# Flatten list-type columns so GDAL can write to GeoJSON cleanly
edges_to_save = edges_utm.copy()
for col in edges_to_save.columns:
    if edges_to_save[col].apply(lambda x: isinstance(x, list)).any():
        edges_to_save[col] = edges_to_save[col].astype(str)

edges_to_save.to_file(output_vector_path, driver="GeoJSON")
print(f"Saved metric road network to: {output_vector_path}")

# %% 4. Visual Verification (Cropped Overlay)
with rasterio.open(scalgo_raster_path) as src:
    streets_plot = edges_utm.to_crs(src.crs)

    buffer = 100
    minx, miny, maxx, maxy = streets_plot.total_bounds
    crop_bounds = (minx - buffer, miny - buffer, maxx + buffer, maxy + buffer)

    window = from_bounds(*crop_bounds, transform=src.transform)
    raster_crop = src.read(
        1, window=window, boundless=True, fill_value=nodata_val
    ).astype(np.float32)
    crop_transform = src.window_transform(window)
    extent = plotting_extent(raster_crop, crop_transform)

# Mask dry and invalid cells
masked_crop = np.ma.masked_where(
    (np.isclose(raster_crop, nodata_val, atol=1e4))
    | (raster_crop <= 0.02)
    | (raster_crop > 10.0)
    | np.isnan(raster_crop),
    raster_crop,
)

width_m = crop_bounds[2] - crop_bounds[0]
height_m = crop_bounds[3] - crop_bounds[1]
aspect_ratio = width_m / max(height_m, 1)

fig, ax = plt.subplots(figsize=(10, max(5, 10 / aspect_ratio)))
ax.imshow(masked_crop, extent=extent, cmap="Blues", alpha=0.6, origin="upper")

# Overlay streets
threshold = 0.05
dry = streets_plot[streets_plot["water_depth_m"] < threshold]
wet = streets_plot[streets_plot["water_depth_m"] >= threshold]

if not dry.empty:
    dry.plot(ax=ax, color="#b0b0b0", linewidth=0.8, alpha=0.5)

if not wet.empty:
    wet.plot(
        ax=ax,
        column="water_depth_m",
        cmap="YlOrRd",
        linewidth=1.5,
        legend=True,
        legend_kwds={"label": "Water Depth (m)", "shrink": 0.7},
    )

ax.set_xlim(extent[0], extent[1])
ax.set_ylim(extent[2], extent[3])
ax.set_title("Wrocław Flood Depth & Drivable Network", fontsize=12)
plt.tight_layout()
plt.show()

# %% State max clearance in cm
threshold = 2  # cm
cm_min_depth = threshold
max_clearance_m = cm_min_depth / 100
m_min_depth = max_clearance_m


# %% 5. A* Application (Physics-Informed Edge Penalties)
def build_routing_graph(gdf_edges, max_clearance_m=max_clearance_m):
    """
    Builds a NetworkX graph with metric coordinates as node positions.
    Edges deeper than max_clearance_m are excluded entirely.
    """
    G = nx.Graph()

    for _, row in gdf_edges.iterrows():
        geom = row.geometry
        depth = row["water_depth_m"]

        if depth >= max_clearance_m:
            continue  # Impassable for standard vehicles

        # Water impedance scaling (penalty multiplier)
        penalty = 1.0 + (depth * 7.0)

        coords = list(geom.coords)
        for i in range(len(coords) - 1):
            p1 = (round(coords[i][0], 2), round(coords[i][1], 2))
            p2 = (round(coords[i + 1][0], 2), round(coords[i + 1][1], 2))

            dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            weight = dist * penalty

            G.add_node(p1, pos=p1)
            G.add_node(p2, pos=p2)
            G.add_edge(p1, p2, weight=weight, length=dist, depth=depth)

    return G


def euclidean_dist(u, v):
    return math.hypot(v[0] - u[0], v[1] - u[1])


# Build graph from metric UTM edges
G_route = build_routing_graph(edges_utm, max_clearance_m=max_clearance_m)
nodes = list(G_route.nodes())

if len(nodes) < 2:
    raise ValueError(
        "Not enough connected traversable nodes to route. Check clearance threshold."
    )

# Test route across largest connected component
largest_cc = max(nx.connected_components(G_route), key=len)
G_sub = G_route.subgraph(largest_cc).copy()
sub_nodes = list(G_sub.nodes())

# Pick two spatially distant nodes
start_node = min(sub_nodes, key=lambda p: p[0] + p[1])
goal_node = max(sub_nodes, key=lambda p: p[0] + p[1])

# Run A*
try:
    path = nx.astar_path(
        G_sub,
        source=start_node,
        target=goal_node,
        heuristic=euclidean_dist,
        weight="weight",
    )
    print(f"Optimal A* path discovered with {len(path)} waypoints.")

    path_geom = LineString(path)
    path_gdf = gpd.GeoDataFrame(geometry=[path_geom], crs=edges_utm.crs)

    # Plot A* Route
    fig, ax = plt.subplots(figsize=(10, 8))
    edges_utm.plot(ax=ax, color="#dddddd", linewidth=0.8)

    wet_utm = edges_utm[edges_utm["water_depth_m"] >= m_min_depth]
    if not wet_utm.empty:
        wet_utm.plot(
            ax=ax,
            color="#ff7f0e",
            linewidth=1.2,
            label=f"Flooded Sections (≥{m_min_depth}m)",
        )

    path_gdf.plot(ax=ax, color="#d62728", linewidth=2.5, label="A* Optimal Route")
    ax.scatter(
        [start_node[0]], [start_node[1]], color="green", s=70, zorder=5, label="Start"
    )
    ax.scatter(
        [goal_node[0]], [goal_node[1]], color="blue", s=70, zorder=5, label="Goal"
    )

    ax.set_title("A* Flood-Penalized Shortest Route (EPSG:32632)", fontsize=12)
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.show()

except nx.NetworkXNoPath:
    print(
        "No viable route found between selected points under current water threshold."
    )

# %%
