{{ config(materialized='table') }}

select
    project_id,
    legal_entity_id,
    business_unit_id,
    project_code,
    project_name,
    start_date,
    end_date,
    status,
    created_at,
    updated_at
from {{ ref('stg_projects') }}