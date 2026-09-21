select
    id as exchange_rate_id,
    from_currency_id,
    to_currency_id,
    rate_date,
    rate_type,
    rate,
    source_system,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_exchangerate') }}