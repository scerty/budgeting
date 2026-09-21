select
    e.encumbrance_id,
    e.organization_id,
    e.legal_entity_id,
    e.budget_version_id,
    e.fiscal_period_id,
    e.group_account_id,
    e.entity_account_id,
    e.branch_id,
    e.department_id,
    e.cost_center_id,
    e.project_id,
    e.currency_id,
    c.currency_code,
    e.amount,
    e.status,
    e.source_system,
    e.source_entity,
    e.source_record_id,
    e.record_hash,
    e.created_at,
    e.updated_at
from {{ ref('stg_encumbrances') }} as e
left join {{ ref('stg_currencies') }} as c
    on e.currency_id = c.currency_id
where lower(e.status) not in ('cancelled', 'released')