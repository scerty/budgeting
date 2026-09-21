select
    id as business_unit_id,
    organization_id,
    code as business_unit_code,
    name as business_unit_name,
    parent_id as parent_business_unit_id,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_businessunit') }}