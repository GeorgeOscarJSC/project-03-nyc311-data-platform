#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=== INGESTION ==="
python3 src/ingestion/fetch_nyc311.py

echo "=== TRANSFORM ==="
python3 src/transform.py

echo "=== POSTGRES LOAD ==="
python3 src/loading/load_postgres.py

echo "=== PIPELINE COMPLETE ==="
