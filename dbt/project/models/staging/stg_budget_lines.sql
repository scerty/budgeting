select
    id as budget_line_id,
    version_id as budget_version_id,
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
    amount,
    currency_id,
    budget_owner_id,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_budgetline') }}