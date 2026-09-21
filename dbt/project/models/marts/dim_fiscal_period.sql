{{ config(materialized='table') }}

select
    p.fiscal_period_id,
    p.fiscal_calendar_id,
    c.organization_id,
    p.fiscal_period_code,
    p.fiscal_period_name,
    p.period_type,
    p.start_date,
    p.end_date,
    extract(year from p.start_date)::integer as fiscal_year,
    extract(quarter from p.start_date)::integer as fiscal_quarter,
    extract(month from p.start_date)::integer as fiscal_month,
    p.status,
    p.is_open_for_actuals,
    p.is_open_for_planning,
    p.created_at,
    p.updated_at
from {{ ref('stg_fiscal_periods') }} as p
left join {{ ref('stg_fiscal_calendars') }} as c
    on p.fiscal_calendar_id = c.fiscal_calendar_id