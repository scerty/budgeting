select
    id as department_branch_assignment_id,
    department_id,
    branch_id,
    valid_from,
    valid_to,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_departmentbranchassignment') }}