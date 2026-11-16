# EIA Electricity Pipeline

An end-to-end pipeline that pulls U.S. retail electricity data (price, revenue, sales, customer counts by state and sector, monthly) from the U.S. Energy Information Administration's API v2, lands it in BigQuery, and models it with dbt.

**Status:** working end to end. Ingests the EIA retail-sales route, loads it to BigQuery, and builds and tests the staging model in dbt.

**Dashboard:** [Residential Electricity Prices: Colorado vs. Texas](https://public.tableau.com/app/profile/brian.curran/viz/ResidentialElectricityPricesColoradovs_Texas/EIADashboard) (Tableau Public, built on `mart_price_yoy`; refreshed manually from a CSV export)

## Architecture

```
EIA API v2 ──► src/ingest_eia.py ──► data/raw/*.json (snapshot)
                                 └─► BigQuery eia_raw.retail_sales_raw
                                          │
                                          ▼
                              dbt staging: stg_eia_retail_sales
                              (typed, deduplicated, tested)
```

## Setup

1. Get a free API key at https://www.eia.gov/opendata/
2. Create a GCP project with BigQuery enabled.
3. Copy `.env.example` to `.env` and fill in the values.
4. Create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Run

```bash
# Fetch and save locally only
python src/ingest_eia.py --states CO TX --start 2020-01 --dry-run

# Fetch and load to BigQuery
python src/ingest_eia.py --states CO TX --start 2020-01

# Tests
pytest

# dbt (from dbt/)
dbt deps
dbt build
```

## Design decisions

- **Raw snapshot before load.** Every run writes the untouched API payload to disk first, so a bad load can be traced back to the exact response.
- **Append-only raw table, deduplicated in dbt.** Re-running ingest doesn't destroy history; the staging model keeps the latest load per state, sector, and month.
- **Tests on the grain.** The staging model asserts uniqueness on period, state, and sector.

## Open items

- [x] Stamp each raw row with `_loaded_at` at load time
- [x] Add a GitHub Actions workflow to run ingest on a monthly schedule
- [x] Add a marts model (`mart_price_yoy`) with year-over-year price change
- [x] Add a Tableau Public dashboard on `mart_price_yoy`
- [ ] Add a Power BI version of the dashboard
- [x] Add a data freshness check on the raw table

## Sources

- EIA API v2 documentation: https://www.eia.gov/opendata/documentation.php
