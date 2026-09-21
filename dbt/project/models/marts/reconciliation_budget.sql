{{ config(materialized='table') }}

with source_lines as (

    select
        budget_version_id,
        count(*) as source_line_count,
        sum(amount) as source_amount
    from {{ ref('stg_budget_lines') }}
    group by budget_version_id

), published_lines as (

    select
        budget_version_id,
        count(*) as published_line_count,
        sum(amount) as published_amount
    from {{ ref('fact_budget') }}
    group by budget_version_id

)

select
    s.budget_version_id,
    s.source_line_count,
    coalesce(p.published_line_count, 0) as published_line_count,
    s.source_amount,
    coalesce(p.published_amount, 0) as published_amount,
    coalesce(p.published_line_count, 0) - s.source_line_count as row_difference,
    coalesce(p.published_amount, 0) - s.source_amount as amount_difference,
    coalesce(p.published_line_count, 0) = s.source_line_count
        and coalesce(p.published_amount, 0) = s.source_amount as is_reconciled
from source_lines as s
left join published_lines as p
    on s.budget_version_id = p.budget_version_id