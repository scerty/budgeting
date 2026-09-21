{{ config(materialized='view') }}

select
    e.expense_id as source_record_id,
    e.source_system,
    e.source_entity,
    e.entity_account_id,
    e.group_account_id,
    e.record_hash,
    'missing_account_mapping' as exception_reason,
    'stg_expenses' as source_model,
    current_timestamp as discovered_at
from {{ ref('stg_expenses') }} as e
where e.is_deleted is not true
  and e.entity_account_id is null
  and e.group_account_id is null