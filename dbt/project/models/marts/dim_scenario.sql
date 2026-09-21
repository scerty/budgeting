{{ config(materialized='table') }}

select
    scenario_id,
    organization_id,
    scenario_code,
    scenario_name,
    scenario_type,
    description,
    status,
    is_active,
    created_at,
    updated_at
from {{ ref('stg_scenarios') }}