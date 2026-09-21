{{ config(materialized='view') }}

select
    e.expense_id as source_record_id,
    e.source_system,
    e.source_entity,
    e.legal_entity_id,
    e.branch_id,
    e.department_id,
    e.cost_center_id,
    e.project_id,
    case
        when e.branch_id is not null and b.legal_entity_id is distinct from e.legal_entity_id
            then 'branch_entity_mismatch'
        when e.department_id is not null and d.legal_entity_id is distinct from e.legal_entity_id
            then 'department_entity_mismatch'
        when e.cost_center_id is not null and cc.legal_entity_id is distinct from e.legal_entity_id
            then 'cost_center_entity_mismatch'
        when e.project_id is not null and p.legal_entity_id is distinct from e.legal_entity_id
            then 'project_entity_mismatch'
        else 'invalid_effective_assignment'
    end as exception_reason,
    'stg_expenses' as source_model,
    current_timestamp as discovered_at
from {{ ref('stg_expenses') }} as e
left join {{ ref('stg_branches') }} as b
    on e.branch_id = b.branch_id
left join {{ ref('stg_departments') }} as d
    on e.department_id = d.department_id
left join {{ ref('stg_cost_centers') }} as cc
    on e.cost_center_id = cc.cost_center_id
left join {{ ref('stg_projects') }} as p
    on e.project_id = p.project_id
where e.is_deleted is not true
  and (
      (e.branch_id is not null and b.legal_entity_id is distinct from e.legal_entity_id)
      or (e.department_id is not null and d.legal_entity_id is distinct from e.legal_entity_id)
      or (e.cost_center_id is not null and cc.legal_entity_id is distinct from e.legal_entity_id)
      or (e.project_id is not null and p.legal_entity_id is distinct from e.legal_entity_id)
  )