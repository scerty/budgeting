select
    id as payment_id,
    organization_id,
    legal_entity_id,
    direction,
    supplier_id,
    customer_id,
    payment_reference,
    payment_date,
    currency_id,
    amount,
    status,
    description,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_payment') }}