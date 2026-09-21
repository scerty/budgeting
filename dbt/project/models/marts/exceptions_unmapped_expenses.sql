{{ config(materialized='view') }}

select
    e.expense_id as source_record_id,
    e.source_system,
    e.source_entity,
    e.record_hash,
    case
        when e.legal_entity_id is null then 'missing_legal_entity'
        when e.department_id is null then 'missing_department'
        when e.group_account_id is null and e.entity_account_id is null
            then 'missing_account_mapping'
        else 'unmapped_expense'
    end as exception_reason,
    'stg_expenses' as source_model,
    current_timestamp as discovered_at
from {{ ref('stg_expenses') }} as e
where e.is_deleted is not true
  and (
      e.legal_entity_id is null
      or e.department_id is null
      or (e.group_account_id is null and e.entity_account_id is null)
  )