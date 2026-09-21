{{ config(materialized='table') }}

select
    currency_id,
    currency_code,
    currency_name,
    symbol,
    decimal_places,
    is_active,
    created_at,
    updated_at
from {{ ref('stg_currencies') }}