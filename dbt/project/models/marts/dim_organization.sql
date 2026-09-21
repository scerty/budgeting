{{ config(materialized='table') }}

select
    organization_id,
    organization_code,
    legal_name,
    display_name,
    default_reporting_currency_id,
    default_fiscal_calendar_id,
    timezone,
    status,
    created_at,
    updated_at
from {{ ref('stg_organizations') }}