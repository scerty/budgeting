{{ config(materialized='table') }}

select
    v.scenario_version_id,
    v.scenario_id,
    s.organization_id,
    s.scenario_code,
    s.scenario_name,
    v.scenario_version_code,
    v.scenario_version_name,
    v.version_number,
    v.status,
    v.based_on_scenario_version_id,
    v.is_final,
    v.locked_at,
    v.created_at,
    v.updated_at
from {{ ref('stg_scenario_versions') }} as v
left join {{ ref('stg_scenarios') }} as s
    on v.scenario_id = s.scenario_id