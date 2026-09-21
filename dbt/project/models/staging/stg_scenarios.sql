select
    id as scenario_id,
    organization_id,
    code as scenario_code,
    name as scenario_name,
    scenario_type,
    description,
    status,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_scenario') }}