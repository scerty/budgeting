{{ config(materialized='table') }}

with expense_summary as (

    select
        branch_id,
        count(*) as expense_count,
        sum(amount) as total_expenses
    from {{ ref('fact_expenses') }}
    group by branch_id

)

select
    b.branch_id,
    b.branch_code,
    b.branch_name,
    b.city,
    coalesce(e.expense_count, 0) as expense_count,
    coalesce(e.total_expenses, 0) as total_expenses

from {{ ref('dim_branch') }} as b

left join expense_summary as e
    on b.branch_id = e.branch_id