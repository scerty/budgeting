select
    b.budget_line_id,
    b.budget_version_id,
    v.budget_plan_id,
    p.organization_id,
    p.fiscal_calendar_id,
    v.budget_version_code,
    v.version_type,
    v.scenario,
    v.scenario_version_id,
    v.status as budget_status,
    b.legal_entity_id,
    b.fiscal_period_id,
    b.group_account_id,
    b.entity_account_id,
    b.branch_id,
    b.department_id,
    b.cost_center_id,
    b.profit_center_id,
    b.business_unit_id,
    b.project_id,
    b.amount,
    c.currency_code,
    b.budget_owner_id,
    b.created_at,
    b.updated_at
from {{ ref('stg_budget_lines') }} as b
left join {{ ref('stg_budget_versions') }} as v
    on b.budget_version_id = v.budget_version_id
left join {{ ref('stg_budget_plans') }} as p
    on v.budget_plan_id = p.budget_plan_id
left join {{ ref('stg_currencies') }} as c
    on b.currency_id = c.currency_id