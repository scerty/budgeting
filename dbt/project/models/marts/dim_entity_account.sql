{{ config(materialized='table') }}

select
    entity_account_id,
    legal_entity_id,
    entity_account_code,
    entity_account_name,
    account_type,
    normal_balance,
    parent_entity_account_id,
    is_posting_allowed,
    is_active,
    created_at,
    updated_at
from {{ ref('stg_entity_accounts') }}