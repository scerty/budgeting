select
    id as account_mapping_id,
    mapping_version_id,
    entity_account_id,
    group_account_id,
    mapping_type,
    allocation_percentage,
    review_status,
    reviewed_by_id,
    reviewed_at,
    notes,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_accountmapping') }}