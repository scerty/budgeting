{{ config(materialized='table') }}

select
    tax_code_id,
    organization_id,
    country_id,
    tax_code,
    tax_code_name,
    tax_type,
    is_active,
    created_at,
    updated_at
from {{ ref('stg_tax_codes') }}