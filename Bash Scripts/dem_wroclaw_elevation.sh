%% bash script for downloading DEM elevation raster
# Variables
API_KEY="YOUR_API_KEY_HERE"
BBOX="16.85 52.22 0.5 0.5"  # lon min lat min lon max lat max
FORMAT="geotiff"
RESOLUTION=30

# Convert bbox to geometry_id (if you already have it, skip this step)
# Here we directly request elevation data for the bbox using a GeoJSON bbox
GEOJSON=$(cat <<'EOF'
{"type":"Polygon","coordinates":[[[$(echo $BBOX | awk '{print $1,$4}'),[$(echo $BBOX | awk '{print $3,$2}')]]]}
EOF
)

# Request elevation data
curl -s -H "X-API-Key: $API_KEY" \
  "https://www.observearth.com/api/dem" \
  --data-urlencode "geometry=$GEOJSON" \
  --data-urlencode "outputFormat=$FORMAT" \
  --data-urlencode "resolution=$RESOLUTION" \
  -o dem_output.tif

echo "DEM data saved to dem_output.tif"