{{ config(materialized='table') }}

select
    customer_id,
    organization_id,
    customer_code,
    customer_name,
    legal_name,
    country_id,
    tax_registration_number,
    default_currency_id,
    email,
    is_active,
    created_at,
    updated_at
from {{ ref('stg_customers') }}