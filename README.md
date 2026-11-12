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

## Run Pipeline

```bash
./run_pipeline.sh

## Database
Database: project03_nyc311

Main table: nyc311_requests

Reporting view: agency_performance
Reporting Query
SELECT *
FROM agency_performance
ORDER BY total_requests DESC;

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
  EOF
  
