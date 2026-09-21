select
    id as currency_id,
    upper(trim(code)) as currency_code,
    name as currency_name,
    symbol,
    decimal_places,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_currency') }}