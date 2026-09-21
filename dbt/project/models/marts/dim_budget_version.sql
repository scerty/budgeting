{{ config(materialized='table') }}

select
    v.budget_version_id,
    v.budget_plan_id,
    p.organization_id,
    p.fiscal_calendar_id,
    v.budget_version_code,
    v.budget_version_name,
    v.version_type,
    v.scenario,
    v.scenario_version_id,
    v.status,
    v.approved_at,
    v.created_at,
    v.updated_at
from {{ ref('stg_budget_versions') }} as v
left join {{ ref('stg_budget_plans') }} as p
    on v.budget_plan_id = p.budget_plan_id