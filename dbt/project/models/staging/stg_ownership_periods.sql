select
    id as ownership_period_id,
    organization_id,
    parent_entity_id,
    child_entity_id,
    ownership_percentage,
    control_percentage,
    consolidation_method,
    valid_from,
    valid_to,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_ownershipperiod') }}