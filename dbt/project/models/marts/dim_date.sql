{{ config(materialized='table') }}

with date_sources as (

    select expense_date as date_day
    from {{ ref('stg_expenses') }}
    where expense_date is not null

    union all

    select posting_date as date_day
    from {{ ref('stg_journal_lines') }}
    where posting_date is not null

),

date_bounds as (

    select
        min(date_day) as min_date,
        max(date_day) as max_date
    from date_sources

),

calendar as (

    select generate_series(
        min_date,
        max_date,
        interval '1 day'
    )::date as date_day
    from date_bounds
    where min_date is not null
      and max_date is not null

)

select
    to_char(date_day, 'YYYYMMDD')::integer as date_key,
    date_day,
    extract(year from date_day)::integer as year,
    extract(quarter from date_day)::integer as quarter,
    extract(month from date_day)::integer as month_number,
    trim(to_char(date_day, 'Month')) as month_name,
    extract(day from date_day)::integer as day_of_month,
    extract(isodow from date_day)::integer as day_of_week
from calendar
order by date_day