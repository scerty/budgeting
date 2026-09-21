{{ config(materialized='view') }}

select
    e.expense_id as source_record_id,
    e.source_system,
    e.source_entity,
    e.legal_entity_id,
    e.group_account_id,
    e.entity_account_id,
    case
        when e.legal_entity_id is not null and le.legal_entity_id is null
            then 'missing_legal_entity_reference'
        when e.group_account_id is not null
            and ga.organization_id is not null
            and le.organization_id <> ga.organization_id
            then 'group_account_organization_mismatch'
        when e.entity_account_id is not null
            and ea.legal_entity_id is not null
            and e.legal_entity_id <> ea.legal_entity_id
            then 'entity_account_legal_entity_mismatch'
        else 'invalid_organization_link'
    end as exception_reason,
    'stg_expenses' as source_model,
    current_timestamp as discovered_at
from {{ ref('stg_expenses') }} as e
left join {{ ref('stg_legal_entities') }} as le
    on e.legal_entity_id = le.legal_entity_id
left join {{ ref('stg_group_accounts') }} as ga
    on e.group_account_id = ga.group_account_id
left join {{ ref('stg_entity_accounts') }} as ea
    on e.entity_account_id = ea.entity_account_id
where e.is_deleted is not true
  and (
      (e.legal_entity_id is not null and le.legal_entity_id is null)
      or (
          e.group_account_id is not null
          and ga.organization_id is not null
          and le.organization_id <> ga.organization_id
      )
      or (
          e.entity_account_id is not null
          and ea.legal_entity_id is not null
          and e.legal_entity_id <> ea.legal_entity_id
      )
  )