{{ config(materialized='table') }}

select
    payment_id,
    organization_id,
    legal_entity_id,
    payment_direction,
    supplier_id,
    customer_id,
    payment_reference,
    payment_date,
    currency_id,
    currency_code,
    amount,
    allocated_amount,
    unallocated_amount,
    allocation_count,
    payment_status,
    description,
    created_at,
    updated_at
from {{ ref('int_payments_allocated') }}