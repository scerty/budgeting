select
    id as planning_driver_id,
    organization_id,
    code as driver_code,
    name as driver_name,
    unit,
    description,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_planningdriver') }}