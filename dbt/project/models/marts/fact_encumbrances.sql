{{ config(materialized='table') }}

select
    encumbrance_id,
    organization_id,
    legal_entity_id,
    budget_version_id,
    fiscal_period_id,
    group_account_id,
    entity_account_id,
    branch_id,
    department_id,
    cost_center_id,
    project_id,
    currency_id,
    currency_code,
    amount,
    status,
    source_system,
    source_entity,
    source_record_id,
    record_hash,
    created_at,
    updated_at
from {{ ref('int_encumbrances_budget_ready') }}