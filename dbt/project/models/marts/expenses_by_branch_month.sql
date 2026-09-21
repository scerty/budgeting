{{ config(materialized='table') }}

select
    f.branch_id as branch_id,
    b.branch_code,
    b.branch_name,
    b.city,
    d.year * 100 + d.month_number as month_key,
    d.year,
    d.month_number,
    d.month_name,
    count(*) as expense_count,
    sum(f.amount) as total_expenses
from {{ ref('fact_expenses') }} as f
inner join {{ ref('dim_branch') }} as b
    on f.branch_id = b.branch_id
inner join {{ ref('dim_date') }} as d
    on f.date_key = d.date_key
group by
    f.branch_id,
    b.branch_code,
    b.branch_name,
    b.city,
    month_key,
    d.year,
    d.month_number,
    d.month_name
order by
    b.branch_code,
    d.year,
    d.month_number
