%% bash script insert the last print section into bbox!!

set -euo pipefail
BBOX="16.80,51.02,17.18,51.21"
PBF_URL="https://download.geofabrik.de/europe/poland/dolnoslaskie-latest.osm.pbf"

echo "1. Downloading Lower Silesian PBF extract..."
curl -s -L -o dolnoslaskie.osm.pbf "$PBF_URL"

echo "2. Clipping to Wrocław bounding box..."
osmium extract --bbox "$BBOX" dolnoslaskie.osm.pbf -o wroclaw.osm.pbf --overwrite

echo "3. Extracting street network lines using ogr2ogr..."
# Extracts lines where 'highway' tag is set
ogr2ogr -f GPKG wroclaw_streets.gpkg wroclaw.osm.pbf \
    lines \
    -where "highway IS NOT NULL" \
    -nln streets

echo "4. Converting to GeoDataFrame in Python..."
# Clean up intermediate files if desired
rm -f dolnoslaskie.osm.pbf wroclaw.osm.pbf
echo "Done! Final dataset saved to wroclaw_streets.gpkg"