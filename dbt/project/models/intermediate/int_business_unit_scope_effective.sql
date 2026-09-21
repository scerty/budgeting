select
    entity_business_unit_assignment_id,
    legal_entity_id,
    business_unit_id,
    valid_from,
    valid_to,
    valid_from <= current_date
        and (valid_to is null or valid_to >= current_date) as is_current,
    created_at,
    updated_at
from {{ ref('stg_entity_business_unit_assignments') }}