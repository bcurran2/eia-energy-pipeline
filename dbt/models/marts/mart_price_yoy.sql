-- Marts: monthly retail price with the change from the same month last year.
-- LAG(..., 12) looks back 12 rows within each state and sector.

with monthly as (

    select
        period_month,
        state_code,
        state_name,
        sector_code,
        sector_name,
        price_cents_per_kwh
    from {{ ref('stg_eia_retail_sales') }}
    where price_cents_per_kwh is not null

),

with_prior_year as (

    select
        *,
        lag(price_cents_per_kwh, 12) over (
            partition by state_code, sector_code
            order by period_month
        ) as price_12m_prior
    from monthly

)

select
    period_month,
    state_code,
    state_name,
    sector_code,
    sector_name,
    price_cents_per_kwh,
    price_12m_prior,
    round(price_cents_per_kwh - price_12m_prior, 2)                         as yoy_change_cents,
    safe_divide(price_cents_per_kwh - price_12m_prior, price_12m_prior)     as yoy_change_pct
from with_prior_year