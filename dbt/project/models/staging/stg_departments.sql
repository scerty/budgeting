select
    id as department_id,
    code as department_code,
    name as department_name,
    branch_id,
    legal_entity_id,
    parent_id as parent_department_id,
    manager_id,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_department') }}