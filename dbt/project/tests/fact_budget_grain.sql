select
    budget_version_id,
    legal_entity_id,
    fiscal_period_id,
    group_account_id,
    entity_account_id,
    branch_id,
    department_id,
    cost_center_id,
    profit_center_id,
    business_unit_id,
    project_id,
    count(*) as row_count
from {{ ref('fact_budget') }}
group by
    budget_version_id,
    legal_entity_id,
    fiscal_period_id,
    group_account_id,
    entity_account_id,
    branch_id,
    department_id,
    cost_center_id,
    profit_center_id,
    business_unit_id,
    project_id
having count(*) > 1