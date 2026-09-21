{{ config(materialized='table') }}

with source_facts as (

    select
        calculation_run_id,
        count(*) as source_fact_count,
        sum(amount) as source_amount
    from {{ ref('stg_planning_facts') }}
    group by calculation_run_id

), published_facts as (

    select
        calculation_run_id,
        count(*) as published_fact_count,
        sum(amount) as published_amount
    from {{ ref('fact_planning') }}
    group by calculation_run_id

), runs as (

    select calculation_run_id, status
    from {{ ref('stg_calculation_runs') }}

)

select
    s.calculation_run_id,
    r.status as calculation_run_status,
    s.source_fact_count,
    coalesce(p.published_fact_count, 0) as published_fact_count,
    s.source_amount,
    coalesce(p.published_amount, 0) as published_amount,
    coalesce(p.published_fact_count, 0) - s.source_fact_count as row_difference,
    coalesce(p.published_amount, 0) - s.source_amount as amount_difference,
    lower(r.status) <> 'succeeded'
        or (
            coalesce(p.published_fact_count, 0) = s.source_fact_count
            and coalesce(p.published_amount, 0) = s.source_amount
        ) as is_reconciled
from source_facts as s
inner join runs as r
    on s.calculation_run_id = r.calculation_run_id
left join published_facts as p
    on s.calculation_run_id = p.calculation_run_id