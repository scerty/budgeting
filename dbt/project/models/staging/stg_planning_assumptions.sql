select
    id as planning_assumption_id,
    organization_id,
    code as assumption_code,
    name as assumption_name,
    value_type,
    numeric_value,
    text_value,
    unit,
    currency_id,
    valid_from,
    valid_to,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_planningassumption') }}