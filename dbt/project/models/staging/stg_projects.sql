select
    id as project_id,
    legal_entity_id,
    business_unit_id,
    code as project_code,
    name as project_name,
    start_date,
    end_date,
    status,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_project') }}