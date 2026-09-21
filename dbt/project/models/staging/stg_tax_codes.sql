select
    id as tax_code_id,
    organization_id,
    country_id,
    code as tax_code,
    name as tax_code_name,
    tax_type,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_taxcode') }}