import http.client
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OUTPUT = BASE / "data/bronze"
OUTPUT.mkdir(parents=True, exist_ok=True)


LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "1"))
if not 1 <= LOOKBACK_DAYS <= 7:
    raise ValueError("LOOKBACK_DAYS must be between 1 and 7")

# 1. Đọc checkpoint từ PostgreSQL
result = subprocess.run(
    [
        "docker", "exec", "ecdp-postgres",
        "psql", "-X", "-At",
        "-U", "data_engineer",
        "-d", "project03_nyc311",
        "-c", f"""
            SELECT (MAX(created_date) - INTERVAL '{LOOKBACK_DAYS} days')::text
            FROM nyc311_requests;
        """
    ],
    capture_output=True,
    text=True,
    check=True
)

checkpoint = result.stdout.strip()
if not checkpoint:
    raise RuntimeError("Database chưa có checkpoint")

checkpoint = checkpoint.replace(" ", "T")
print("Checkpoint:", checkpoint)

# 2. Tải dữ liệu theo từng trang 1.000 bản ghi
rows = []
offset = 0
page_size = 1000

while True:
    params = urllib.parse.urlencode({
        "$where": f"created_date >= '{checkpoint}'",
        "$order": "created_date ASC, unique_key ASC",
        "$limit": page_size,
        "$offset": offset
    })

    url = (
        "https://data.cityofnewyork.us/resource/"
        "erm2-nwe9.json?" + params
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=180) as response:
                batch = json.load(response)
            break
        except (urllib.error.HTTPError,
                urllib.error.URLError,
                http.client.IncompleteRead,
                TimeoutError, ConnectionError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and (
                exc.code not in (429, 500, 502, 503, 504)
            ):
                raise
            if attempt == 2:
                raise
            print(f"API error: {exc}. Retrying...")
            time.sleep(5 * (attempt + 1))

    rows.extend(batch)
    print(f"Fetched: {len(rows)}")

    if len(batch) < page_size:
        break

    offset += page_size

# 3. Lưu Bronze sau khi tải hoàn tất
today = datetime.now(timezone.utc).strftime("%Y%m%d")
filename = OUTPUT / f"nyc311_daily_{today}.json"
temporary = filename.with_suffix(".json.tmp")

with temporary.open("w") as f:
    json.dump(rows, f)

temporary.replace(filename)

print("File:", filename)
print("Total records:", len(rows))
print("INCREMENTAL INGESTION COMPLETE")
