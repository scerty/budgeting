select
    id as payment_allocation_id,
    payment_id,
    invoice_id,
    amount,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_paymentallocation') }}