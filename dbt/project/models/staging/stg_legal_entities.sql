select
    id as legal_entity_id,
    organization_id,
    code as entity_code,
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
from {{ source('postgres_app', 'finance_legalentity') }}