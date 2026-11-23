#!/usr/bin/env bash
set -euo pipefail

MIN_LON="$1"
MIN_LAT="$2"
MAX_LON="$3"
MAX_LAT="$4"

BBOX="${MIN_LON},${MIN_LAT},${MAX_LON},${MAX_LAT}"

PBF_URL="https://download.geofabrik.de/europe/poland/dolnoslaskie-latest.osm.pbf"
OUTPUT_GPKG="Output files cached/wroclaw_streets.gpkg"

echo "1. Downloading Wrocław PBF extract..."
curl -s -L -o dolnoslaskie.osm.pbf "$PBF_URL"

echo "2. Clipping to bounding box ($BBOX)..."
osmium extract --bbox "$BBOX" dolnoslaskie.osm.pbf -o wroclaw.osm.pbf --overwrite

echo "3. Extracting street network lines using ogr2ogr..."
mkdir -p "Output files cached"
ogr2ogr -f GPKG "$OUTPUT_GPKG" onondaga_county.osm.pbf \
    lines \
    -where "highway IS NOT NULL AND highway NOT IN ('path','footway','pedestrian','steps','proposed','cycleway','elevator','track','platform','rest_area')" \
    -nln streets

echo "4. Cleaning up intermediate files..."
rm -f dolnoslaskie.osm.pbf wroclaw.osm.pbf
echo "Done! Final dataset saved to $OUTPUT_GPKG"