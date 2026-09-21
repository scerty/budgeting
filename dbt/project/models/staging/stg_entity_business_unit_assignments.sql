select
    id as entity_business_unit_assignment_id,
    legal_entity_id,
    business_unit_id,
    valid_from,
    valid_to,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_entitybusinessunitassignment') }}