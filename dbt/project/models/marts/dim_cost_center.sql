{{ config(materialized='table') }}

select
    cost_center_id,
    legal_entity_id,
    cost_center_code,
    cost_center_name,
    parent_cost_center_id,
    branch_id,
    department_id,
    is_active,
    created_at,
    updated_at
from {{ ref('stg_cost_centers') }}