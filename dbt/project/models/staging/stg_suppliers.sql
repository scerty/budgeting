select
    id as supplier_id,
    organization_id,
    code as supplier_code,
    name as supplier_name,
    legal_name,
    country_id,
    tax_registration_number,
    default_currency_id,
    email,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_supplier') }}