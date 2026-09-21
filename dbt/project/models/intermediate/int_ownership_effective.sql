select
    ownership_period_id,
    organization_id,
    parent_entity_id,
    child_entity_id,
    ownership_percentage,
    control_percentage,
    consolidation_method,
    valid_from,
    valid_to,
    valid_from <= current_date
        and (valid_to is null or valid_to >= current_date) as is_current,
    created_at,
    updated_at
from {{ ref('stg_ownership_periods') }}