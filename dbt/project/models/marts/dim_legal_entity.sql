{{ config(materialized='table') }}

select
    legal_entity_id,
    organization_id,
    entity_code,
    legal_name,
    short_name,
    country_id,
    tax_registration_number,
    functional_currency_id,
    reporting_currency_id,
    fiscal_calendar_id,
    parent_entity_id,
    consolidation_method,
    valid_from,
    valid_to,
    status,
    created_at,
    updated_at
from {{ ref('stg_legal_entities') }}