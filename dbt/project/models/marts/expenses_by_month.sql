{{ config(materialized='table') }}

select
    d.year * 100 + d.month_number as month_key,
    d.year,
    d.month_number,
    d.month_name,
    count(*) as expense_count,
    sum(f.amount) as total_expenses
from {{ ref('fact_expenses') }} as f
inner join {{ ref('dim_date') }} as d
    on f.date_key = d.date_key
group by
    month_key,
    d.year,
    d.month_number,
    d.month_name
order by
    d.year,
    d.month_number
