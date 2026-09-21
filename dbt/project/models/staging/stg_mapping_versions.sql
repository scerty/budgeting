select
    id as mapping_version_id,
    organization_id,
    code as mapping_version_code,
    name as mapping_version_name,
    valid_from,
    valid_to,
    status,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_mappingversion') }}