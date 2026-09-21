{{ config(materialized='table') }}

select
    department_id,
    department_code,
    department_name,
    branch_id
    , legal_entity_id
    , parent_department_id
    , is_active
from {{ ref('stg_departments') }}