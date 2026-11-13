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
bronze_path=$(
    set -o pipefail
    python3 -u src/ingestion/fetch_nyc311.py |
        tee -a  /dev/stderr |
        sed -n 's/^File: //p'
)

if [ ! -f "$bronze_path" ]; then
    echo "ERROR: The downloader did not report a valid Bronze file." >&2
    exit 1
fi

echo "=== TRANSFORM ==="
python3 src/transform.py "$bronze_path"

echo "=== POSTGRES LOAD ==="
python3 src/loading/load_postgres.py

echo "=== PIPELINE COMPLETE ==="
