{{ config(materialized='table') }}

select
    profit_center_id,
    legal_entity_id,
    profit_center_code,
    profit_center_name,
    branch_id,
    business_unit_id,
    is_active,
    created_at,
    updated_at
from {{ ref('stg_profit_centers') }}