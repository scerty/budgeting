{{ config(materialized='table') }}

select
    driver_value_id,
    planning_driver_id,
    organization_id,
    scenario_version_id,
    fiscal_period_id,
    legal_entity_id,
    branch_id,
    department_id,
    project_id,
    value,
    currency_id,
    source,
    created_at,
    updated_at
from {{ ref('int_planning_driver_values') }}