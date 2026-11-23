#!/usr/bin/env bash
set -euo pipefail

# Onondaga County, NY Bounding Box: (min_lon, min_lat, max_lon, max_lat)
# Extents roughly: W -76.498, S 42.787, E -75.885, N 43.267
BBOX="-76.50,42.78,-75.88,43.27"
PBF_URL="https://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf"

echo "1. Downloading New York state PBF extract..."
curl -s -L -o new_york.osm.pbf "$PBF_URL"

echo "2. Clipping to Onondaga County bounding box..."
osmium extract --bbox "$BBOX" new_york.osm.pbf -o onondaga_county.osm.pbf --overwrite

echo "3. Extracting drivable street network lines using ogr2ogr..."
# Extracts lines where 'highway' tag is set
ogr2ogr -f GPKG onondaga_streets.gpkg onondaga_county.osm.pbf \
    lines \
    -where "highway IS NOT NULL" \
    -nln streets

echo "4. Cleaning up raw intermediate files..."
rm -f new_york.osm.pbf onondaga_county.osm.pbf

echo "Done! Final dataset saved to onondaga_streets.gpkg"