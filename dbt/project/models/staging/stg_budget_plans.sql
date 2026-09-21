select
    id as budget_plan_id,
    organization_id,
    fiscal_calendar_id,
    code as budget_plan_code,
    name as budget_plan_name,
    description,
    status,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_budgetplan') }}