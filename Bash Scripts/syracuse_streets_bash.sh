#!/usr/bin/env bash
set -euo pipefail

MIN_LON="$1"
MIN_LAT="$2"
MAX_LON="$3"
MAX_LAT="$4"

BBOX="${MIN_LON},${MIN_LAT},${MAX_LON},${MAX_LAT}"

PBF_URL="https://download.geofabrik.de/north-america/us/new-york-latest.osm.pbf"
OUTPUT_GPKG="Output files cached/syracuse_streets.gpkg"

echo "1. Downloading New York state PBF extract..."
curl -s -L -o new_york.osm.pbf "$PBF_URL"

echo "2. Clipping to Onondaga County bounding box..."
osmium extract --bbox "$BBOX" new_york.osm.pbf -o onondaga_county.osm.pbf --overwrite

echo "3. Extracting drivable street network lines using ogr2ogr..."
# Extracts lines where 'highway' tag is set
ogr2ogr -f GPKG "$OUTPUT_GPKG" onondaga_county.osm.pbf \
    lines \
    -where "highway IS NOT NULL AND highway NOT IN ('path','footway','pedestrian','steps','proposed','cycleway','elevator','track','platform','rest_area')" \
    -nln streets

echo "4. Cleaning up raw intermediate files..."
rm -f new_york.osm.pbf onondaga_county.osm.pbf

echo "Done! Final dataset saved to $OUTPUT_GPKG"