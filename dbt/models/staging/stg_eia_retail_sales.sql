-- Staging: one clean row per state, sector, and month.
-- Reads the raw table loaded by src/ingest_eia.py.

with source as (

    select * from {{ source('eia_raw', 'retail_sales_raw') }}

),

typed as (

    select
        parse_date('%Y-%m', period)                 as period_month,
        stateid                                     as state_code,
        stateDescription                            as state_name,
        sectorid                                    as sector_code,
        sectorName                                  as sector_name,
        cast(price as float64)                      as price_cents_per_kwh,
        cast(revenue as float64)                    as revenue_thousand_usd,
        cast(sales as float64)                      as sales_mwh,
        cast(customers as float64)                  as customer_count,
        _loaded_at
    from source

),

deduped as (

    -- Re-running ingest appends rows again; keep the most recent load per key.
    select *
    from typed
    qualify row_number() over (
        partition by period_month, state_code, sector_code
        order by _loaded_at desc
    ) = 1

)

select * from deduped
