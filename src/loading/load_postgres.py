import csv
import io
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SILVER = BASE / "data/silver/nyc311_valid.jsonl"

rows = [
    json.loads(line)
    for line in SILVER.read_text().splitlines()
    if line.strip()
]

sql = """
BEGIN;

CREATE TEMP TABLE incoming (raw_data JSONB);

COPY incoming (raw_data) FROM STDIN WITH (FORMAT csv);

INSERT INTO nyc311_requests (
    unique_key, created_date, closed_date,
    agency, complaint_type, status, borough, raw_data
)
SELECT DISTINCT ON (raw_data->>'unique_key')
    raw_data->>'unique_key',
    NULLIF(raw_data->>'created_date', '')::timestamp,
    NULLIF(raw_data->>'closed_date', '')::timestamp,
    raw_data->>'agency',
    raw_data->>'complaint_type',
    raw_data->>'status',
    raw_data->>'borough',
    raw_data
FROM incoming
ORDER BY raw_data->>'unique_key',
         NULLIF(raw_data->>'resolution_action_updated_date', '')::timestamp DESC NULLS LAST,
         NULLIF(raw_data->>'closed_date', '')::timestamp DESC NULLS LAST
ON CONFLICT (unique_key)
DO UPDATE SET
    created_date = EXCLUDED.created_date,
    closed_date = EXCLUDED.closed_date,
    agency = EXCLUDED.agency,
    complaint_type = EXCLUDED.complaint_type,
    status = EXCLUDED.status,
    borough = EXCLUDED.borough,
    raw_data = EXCLUDED.raw_data,
    updated_at = NOW()
WHERE nyc311_requests.raw_data IS DISTINCT FROM EXCLUDED.raw_data;

COMMIT;
"""

# COPY nhận JSONL qua stdin; dùng script psql riêng để
# PostgreSQL xử lý toàn bộ batch trong một transaction.
copy_start = sql.index("COPY incoming")
copy_end = sql.index("INSERT INTO nyc311_requests", copy_start)

prefix = sql[:copy_start]
suffix = sql[copy_end:]

buffer = io.StringIO()
writer = csv.writer(buffer, lineterminator=chr(10))
for row in rows:
    writer.writerow([json.dumps(row, ensure_ascii=False)])
csv_data = buffer.getvalue()

script = (
    prefix
    + "COPY incoming (raw_data) FROM STDIN WITH (FORMAT csv);\n"
    + csv_data
    + "\\.\n"
    + suffix
)

result = subprocess.run(
    [
        "docker", "exec", "-i", "ecdp-postgres",
        "psql", "-X", "-v", "ON_ERROR_STOP=1",
        "-U", "data_engineer",
        "-d", "project03_nyc311"
    ],
    input=script,
    text=True,
    capture_output=True
)

if result.returncode != 0:
    raise RuntimeError(result.stderr)

print(result.stdout)
print(f"Silver records submitted: {len(rows)}")
print("POSTGRES LOAD COMPLETE")
