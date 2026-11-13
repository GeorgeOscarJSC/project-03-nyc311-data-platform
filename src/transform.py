import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

import sys

if len(sys.argv) > 1:
    bronze = Path(sys.argv[1])
else:
    files = list((BASE / "data/bronze").glob("nyc311_daily_*.json"))
    if not files:
        raise FileNotFoundError("No daily Bronze file found")
    bronze = max(files, key=lambda p: p.name)

silver = BASE / "data/silver/nyc311_valid.jsonl"
quarantine = BASE / "data/quarantine/nyc311_invalid.jsonl"

rows = json.loads(bronze.read_text())

valid = []
invalid = []

for row in rows:
    created = row.get("created_date")
    closed = row.get("closed_date")

    if closed and created and closed < created:
        invalid.append({
            **row,
            "_quality_error": "CLOSED_BEFORE_CREATED"
        })
    else:
        valid.append(row)

silver.parent.mkdir(parents=True, exist_ok=True)
quarantine.parent.mkdir(parents=True, exist_ok=True)

for path, records in [
    (silver, valid),
    (quarantine, invalid)
]:
    with path.open("w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

assert len(valid) + len(invalid) == len(rows)

print(f"Bronze: {len(rows)}")
print(f"Silver: {len(valid)}")
print(f"Quarantine: {len(invalid)}")
print("PASS")
