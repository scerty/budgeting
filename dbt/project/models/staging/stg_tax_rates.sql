select
    id as tax_rate_id,
    tax_code_id,
    rate,
    valid_from,
    valid_to,
    is_recoverable,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_taxrate') }}