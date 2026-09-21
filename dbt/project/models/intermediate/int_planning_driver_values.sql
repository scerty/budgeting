select
    v.driver_value_id,
    v.planning_driver_id,
    d.organization_id,
    v.scenario_version_id,
    v.fiscal_period_id,
    v.legal_entity_id,
    v.branch_id,
    v.department_id,
    v.project_id,
    v.value,
    v.currency_id,
    v.source,
    v.created_at,
    v.updated_at
from {{ ref('stg_driver_values') }} as v
inner join {{ ref('stg_planning_drivers') }} as d
    on v.planning_driver_id = d.planning_driver_id
where d.is_active is true