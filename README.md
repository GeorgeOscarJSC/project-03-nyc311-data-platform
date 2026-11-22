# Project 03 — NYC 311 Data Platform

## Architecture

NYC Open Data API
    → Python Ingestion
    → Bronze JSON
    → Silver JSONL + Quarantine
    → PostgreSQL UPSERT
    → SQL Reporting View

## Tech Stack

- Python 3.12
- PostgreSQL 16
- Docker
- Linux cron
- Git


## First-Time Setup

Requirements: Docker, Python 3.12, Linux.

### 1. Create a database password

```bash
printf 'PROJECT03_PG_PASSWORD=%s\n' "$(openssl rand -hex 24)" > .env
chmod 600 .env
```

### 2. Start PostgreSQL

```bash
docker compose up -d
```

### 3. Create the table and reporting view

```bash
docker exec -i project03-postgres psql -U data_engineer -d project03_nyc311 < sql/nyc311_requests.sql

docker exec -i project03-postgres psql -U data_engineer -d project03_nyc311 < sql/agency_performance.sql
```

### 4. Run the first ingestion

```bash
BOOTSTRAP_START=2026-11-19T00:00:00 ./run_pipeline.sh
```

The bootstrap date is an example. Choose an appropriate starting date for your initial historical data load.


## Run Pipeline

```bash
./run_pipeline.sh

```

## Database
Database: project03_nyc311

Main table: nyc311_requests

Reporting view: agency_performance
## Reporting Query

```sql
SELECT *
FROM agency_performance
ORDER BY total_requests DESC;

```

## Scheduling
Daily execution via Linux cron at 08:00
(system local time).

## Monitoring
tail -n 30 pipeline.log

## Current Limitations
- Incremental ingestion uses created_date.
- Older records updated later may be missed.
- API offset pagination may be affected by source changes.
- Pipeline requires Docker and PostgreSQL.
  
