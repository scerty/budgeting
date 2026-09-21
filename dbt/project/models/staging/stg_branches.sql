select
    id as branch_id,
    legal_entity_id,
    country_id,
    code as branch_code,
    name as branch_name,
    city,
    address,
    timezone,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_branch') }}