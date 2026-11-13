#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

mkdir -p data/bronze
exec 9>>data/bronze/.pipeline.lock
flock -n -E 75 9 || {
    code=$?
    if [ "$code" -eq 75 ]; then
        echo "SKIP: Another pipeline run is active."
        exit 0
    fi
    exit "$code"
}

echo "=== INGESTION ==="
python3 src/ingestion/fetch_nyc311.py

echo "=== TRANSFORM ==="
python3 src/transform.py

echo "=== POSTGRES LOAD ==="
python3 src/loading/load_postgres.py

echo "=== PIPELINE COMPLETE ==="
