select
    id as country_id,
    upper(trim(iso_code)) as country_code,
    name as country_name,
    default_currency_id,
    tax_jurisdiction_code,
    timezone,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_country') }}