{{ config(materialized='table') }}

select
    expense_id,
    source_system,
    source_entity,
    source_record_id,
    record_hash,
    department_id,
    branch_id,
    legal_entity_id,
    organization_id,
    entity_account_id,
    group_account_id,
    cost_center_id,
    profit_center_id,
    business_unit_id,
    project_id,
    expense_date,
    to_char(expense_date, 'YYYYMMDD')::integer as date_key,
    amount,
    currency_code,
    currency_master_id,
    description,
    ingested_at,
    source_created_at,
    source_updated_at,
    created_at,
    updated_at
from {{ ref('int_expenses_enriched') }}
where is_deleted is not true