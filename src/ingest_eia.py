"""
Ingest U.S. retail electricity data from the EIA API v2 into BigQuery.

Pipeline stage 1 (raw ingest):
  EIA API -> local raw JSON snapshot -> BigQuery raw table

Usage:
  python src/ingest_eia.py --states CO TX --start 2020-01 --dry-run
  python src/ingest_eia.py --states CO TX --start 2020-01
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

EIA_URL = "https://api.eia.gov/v2/electricity/retail-sales/data/"
PAGE_SIZE = 5000  # EIA caps responses at 5,000 rows
RAW_DIR = Path("data/raw")


def fetch_all_rows(api_key: str, states: list[str], start: str) -> list[dict]:
    """Page through the EIA retail-sales route and return every row."""
    params = {
        "api_key": api_key,
        "frequency": "monthly",
        "data[0]": "price",
        "data[1]": "revenue",
        "data[2]": "sales",
        "data[3]": "customers",
        "start": start,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "length": PAGE_SIZE,
        "offset": 0,
    }
    # Repeated facets: facets[stateid][]=CO&facets[stateid][]=TX
    facet_pairs = [("facets[stateid][]", s) for s in states]

    rows: list[dict] = []
    while True:
        query = list(params.items()) + facet_pairs
        resp = requests.get(EIA_URL, params=query, timeout=60)
        resp.raise_for_status()
        body = resp.json()["response"]
        page = body["data"]
        total = int(body["total"])
        rows.extend(page)
        params["offset"] += len(page)
        if not page or params["offset"] >= total:
            break
    return rows


def write_raw_snapshot(rows: list[dict]) -> Path:
    """Save the untouched API payload so every load can be traced back to a file."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RAW_DIR / f"eia_retail_sales_{stamp}.json"
    path.write_text(json.dumps(rows, indent=2))
    return path


def load_to_bigquery(rows: list[dict]) -> None:
    """Append raw rows to a BigQuery table. Transformations happen later in dbt."""
    from google.cloud import bigquery  # imported here so --dry-run works without GCP

    project = os.environ["GCP_PROJECT"]
    dataset = os.environ.get("BQ_DATASET", "eia_raw")
    table_id = f"{project}.{dataset}.retail_sales_raw"

    client = bigquery.Client(project=project)
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=True,
    )
    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()  # block until the load finishes or raises
    print(f"Loaded {len(rows)} rows into {table_id}")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--states", nargs="+", required=True, help="State codes, e.g. CO TX")
    parser.add_argument("--start", required=True, help="Start period, YYYY-MM")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and save locally; skip BigQuery")
    args = parser.parse_args()

    api_key = os.environ["EIA_API_KEY"]
    rows = fetch_all_rows(api_key, args.states, args.start)
    print(f"Fetched {len(rows)} rows")

    snapshot = write_raw_snapshot(rows)
    print(f"Saved raw snapshot to {snapshot}")

    if not args.dry_run:
        load_to_bigquery(rows)


if __name__ == "__main__":
    main()
