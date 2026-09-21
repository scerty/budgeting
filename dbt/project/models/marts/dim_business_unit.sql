{{ config(materialized='table') }}

select
    business_unit_id,
    organization_id,
    business_unit_code,
    business_unit_name,
    parent_business_unit_id,
    is_active,
    created_at,
    updated_at
from {{ ref('stg_business_units') }}