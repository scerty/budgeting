select
    p.planning_fact_id,
    p.calculation_run_id,
    r.organization_id,
    r.status as calculation_run_status,
    r.started_at as calculation_started_at,
    r.completed_at as calculation_completed_at,
    p.scenario_version_id,
    sv.scenario_id,
    s.scenario_code,
    s.scenario_name,
    p.fiscal_period_id,
    p.legal_entity_id,
    p.group_account_id,
    p.entity_account_id,
    p.branch_id,
    p.department_id,
    p.cost_center_id,
    p.profit_center_id,
    p.business_unit_id,
    p.project_id,
    p.source_kind,
    p.source_calculation_rule_id,
    p.amount,
    p.currency_id,
    c.currency_code,
    p.lineage,
    p.created_at,
    p.updated_at
from {{ ref('stg_planning_facts') }} as p
inner join {{ ref('stg_calculation_runs') }} as r
    on p.calculation_run_id = r.calculation_run_id
inner join {{ ref('stg_scenario_versions') }} as sv
    on p.scenario_version_id = sv.scenario_version_id
inner join {{ ref('stg_scenarios') }} as s
    on sv.scenario_id = s.scenario_id
left join {{ ref('stg_currencies') }} as c
    on p.currency_id = c.currency_id
where lower(r.status) = 'succeeded'