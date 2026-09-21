select
    id as budget_version_id,
    plan_id as budget_plan_id,
    code as budget_version_code,
    name as budget_version_name,
    version_type,
    scenario,
    scenario_version_id,
    status,
    approved_at,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_budgetversion') }}