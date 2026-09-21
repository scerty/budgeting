select
    id as department_entity_assignment_id,
    department_id,
    legal_entity_id,
    valid_from,
    valid_to,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_departmententityassignment') }}