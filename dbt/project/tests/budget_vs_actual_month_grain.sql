select
    organization_id,
    fiscal_period_id,
    legal_entity_id,
    group_account_id,
    entity_account_id,
    branch_id,
    department_id,
    cost_center_id,
    profit_center_id,
    business_unit_id,
    project_id,
    currency_code,
    month_start,
    count(*) as row_count
from {{ ref('budget_vs_actual_month') }}
group by
    organization_id,
    fiscal_period_id,
    legal_entity_id,
    group_account_id,
    entity_account_id,
    branch_id,
    department_id,
    cost_center_id,
    profit_center_id,
    business_unit_id,
    project_id,
    currency_code,
    month_start
having count(*) > 1