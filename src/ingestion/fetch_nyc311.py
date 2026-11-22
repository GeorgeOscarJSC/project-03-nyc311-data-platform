import http.client
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import os

BASE = Path(__file__).resolve().parents[2]
BRONZE = BASE / "data/bronze"
RESUME = BRONZE / ".ingestion_resume"
API = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
PAGE_SIZE = 1000

BRONZE.mkdir(parents=True, exist_ok=True)

def save_json(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False))
    temp.replace(path)

# Khôi phục phiên tải cũ, hoặc tạo phiên mới
meta_file = RESUME / "metadata.json"

if meta_file.exists():
    meta = json.loads(meta_file.read_text())
    print("RESUMING PREVIOUS DOWNLOAD")
else:
    lookback = int(os.getenv("LOOKBACK_DAYS", "1"))
    if not 1 <= lookback <= 7:
        raise ValueError("LOOKBACK_DAYS must be 1..7")

    result = subprocess.run(
        [
            "docker", "exec", "project03-postgres",
            "psql", "-X", "-At",
            "-U", "data_engineer",
            "-d", os.getenv("NYC311_DB", "project03_nyc311"),
            "-c", f"""
                SELECT (
                    MAX(created_date)
                    - INTERVAL '{lookback} days'
                )::text
                FROM nyc311_requests;
            """
        ],
        capture_output=True,
        text=True,
        check=True
    )

    start = result.stdout.strip().replace(" ", "T")
    if not start:
        first_start = os.getenv("BOOTSTRAP_START")
        if not first_start:
            raise RuntimeError(
                "Database is empty. Set BOOTSTRAP_START, for example "
                "2026-11-10T00:00:00."
            )
        start = datetime.strptime(first_start, "%Y-%m-%dT%H:%M:%S").isoformat()

    meta = {
        "start": start,
        "end": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),
        "run_date": datetime.now(timezone.utc).strftime("%Y%m%d"),
        "page_size": PAGE_SIZE
    }

    RESUME.mkdir(parents=True, exist_ok=True)
    save_json(meta_file, meta)

print("Checkpoint:", meta["start"])

# Đọc trang cuối đã lưu
pages = sorted(RESUME.glob("page_*.json"))
page_number = len(pages)
cursor = None

if pages:
    last = json.loads(pages[-1].read_text())
    cursor = last[-1]
    print("Already saved:", sum(
        len(json.loads(p.read_text())) for p in pages
    ))

# Tiếp tục tải bằng Keyset Pagination
while True:
    where = (
        f"created_date >= '{meta['start']}' "
        f"AND created_date <= '{meta['end']}'"
    )

    if cursor:
        date = cursor["created_date"]
        key = cursor["unique_key"]
        where += (
            f" AND (created_date > '{date}' "
            f"OR (created_date = '{date}' "
            f"AND unique_key > '{key}'))"
        )

    params = urllib.parse.urlencode({
        "$where": where,
        "$order": "created_date ASC, unique_key ASC",
        "$limit": meta["page_size"]
    })

    request = urllib.request.Request(
        API + "?" + params,
        headers={"User-Agent": "Project03/1.0"}
    )

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(
                request, timeout=180
            ) as response:
                batch = json.load(response)
            break
        except (
            urllib.error.URLError,
            http.client.IncompleteRead,
            http.client.RemoteDisconnected,
            TimeoutError,
            ConnectionError
        ) as exc:
            if isinstance(exc, urllib.error.HTTPError):
                if exc.code not in (429, 500, 502, 503, 504):
                    raise
            if attempt == 3:
                raise
            print(f"Retry {attempt}/3: {exc}")
            time.sleep(5 * attempt)

    if not batch:
        break

    # Lưu trang thành công trước khi tải trang kế tiếp
    path = RESUME / f"page_{page_number:06d}.json"
    save_json(path, batch)

    page_number += 1
    cursor = batch[-1]
    print(f"Saved page {page_number}: {len(batch)} records")

    if len(batch) < meta["page_size"]:
        break

# Ghép các trang thành file Bronze hoàn chỉnh
file_stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
filename = BRONZE / f"nyc311_daily_{file_stamp}.json"
temp = filename.with_suffix(".json.tmp")

total = 0

with temp.open("w") as f:
    f.write("[")
    first = True

    for page in sorted(RESUME.glob("page_*.json")):
        for row in json.loads(page.read_text()):
            if not first:
                f.write(",")
            json.dump(row, f, ensure_ascii=False)
            first = False
            total += 1

    f.write("]")

temp.replace(filename)
shutil.rmtree(RESUME)

print("File:", filename)
print("Total records:", total)
print("RESUMABLE INGESTION COMPLETE")
