"""Export the mart_price_yoy table to a CSV for the dashboards."""
import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT = os.environ["GCP_PROJECT"]
DATASET = os.environ.get("MART_DATASET", "eia_dev")
OUT = Path("dashboard_data/mart_price_yoy.csv")


def main():
    client = bigquery.Client(project=PROJECT)
    sql = (
        f"select * from `{PROJECT}.{DATASET}.mart_price_yoy` "
        "order by period_month, state_code, sector_code"
    )
    rows = client.query(sql).result()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([field.name for field in rows.schema])
        for row in rows:
            writer.writerow(list(row.values()))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()