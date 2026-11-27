#!/usr/bin/env bash
set -e

exec 9>>data/bronze/.pipeline.lock
flock -n 9 || exit 0
docker exec project03-postgres \
  psql -U data_engineer -d project03_nyc311 -At \
  -c "SELECT unique_key FROM nyc311_requests WHERE status IN ('Open', 'In Progress');" \
  > data/open_request_ids.txt

total=$(wc -l < data/open_request_ids.txt)

for ((start=0; start<total; start+=100)); do
    BATCH_START="$start" python3 src/ingestion/refresh_open_requests.py
    python3 src/transform.py data/bronze/open_requests_refresh.json
    python3 src/loading/load_postgres.py
done
docker exec project03-postgres \
  psql -U data_engineer -d project03_nyc311 \
  -c "COPY (SELECT * FROM agency_performance ORDER BY total_requests DESC) TO STDOUT WITH CSV HEADER" \
  > data/reports/agency_performance.csv
