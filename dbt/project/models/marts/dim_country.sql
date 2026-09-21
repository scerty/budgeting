{{ config(materialized='table') }}

select
    country_id,
    country_code,
    country_name,
    default_currency_id,
    tax_jurisdiction_code,
    timezone,
    created_at,
    updated_at
from {{ ref('stg_countries') }}