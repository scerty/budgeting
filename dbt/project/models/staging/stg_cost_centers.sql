select
    id as cost_center_id,
    legal_entity_id,
    code as cost_center_code,
    name as cost_center_name,
    parent_id as parent_cost_center_id,
    branch_id,
    department_id,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_costcenter') }}