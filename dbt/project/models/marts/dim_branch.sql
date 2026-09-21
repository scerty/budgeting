{{ config(materialized='table') }}

select
    branch_id,
    branch_code,
    branch_name,
    city,
    legal_entity_id,
    country_id,
    is_active
from {{ ref('stg_branches') }}