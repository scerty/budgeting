select
    id as profit_center_id,
    legal_entity_id,
    code as profit_center_code,
    name as profit_center_name,
    branch_id,
    business_unit_id,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_profitcenter') }}