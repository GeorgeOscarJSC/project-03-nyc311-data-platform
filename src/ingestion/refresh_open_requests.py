import time
import urllib.error
import os
import json
import urllib.parse
import urllib.request
from pathlib import Path

base = Path(__file__).resolve().parents[2]
all_ids = (base / "data/open_request_ids.txt").read_text().splitlines()
batch_start = int(os.getenv("BATCH_START", "0"))
batch_size = 100
ids = all_ids[batch_start:batch_start + batch_size]

where = "unique_key IN (" + ",".join(f"'{key}'" for key in ids) + ")"

params = urllib.parse.urlencode({
    "$where": where,
    "$select": "*,:updated_at"
})

url = "https://data.cityofnewyork.us/resource/erm2-nwe9.json?" + params

for attempt in range(3):
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            records = json.load(response)
        break
    except urllib.error.HTTPError as error:
        if error.code != 503 or attempt == 2:
            raise
        time.sleep(5)

output = base / "data/bronze/open_requests_refresh.json"
output.write_text(json.dumps(records))

print("Requested:", len(ids))
print("Returned:", len(records))
