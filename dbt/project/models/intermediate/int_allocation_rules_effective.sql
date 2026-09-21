select
    r.allocation_rule_id,
    r.organization_id,
    r.allocation_rule_code,
    r.allocation_rule_name,
    r.basis,
    r.source_legal_entity_id,
    r.source_group_account_id,
    r.source_cost_center_id,
    r.valid_from,
    r.valid_to,
    r.status,
    coalesce(sum(l.allocation_percentage), 0) as total_allocation_percentage,
    count(l.allocation_rule_line_id) as allocation_line_count,
    coalesce(sum(l.allocation_percentage), 0) = 100 as is_fully_allocated,
    lower(r.status) = 'approved'
        and r.valid_from <= current_date
        and (r.valid_to is null or r.valid_to >= current_date) as is_effective
from {{ ref('stg_allocation_rules') }} as r
left join {{ ref('stg_allocation_rule_lines') }} as l
    on r.allocation_rule_id = l.allocation_rule_id
group by
    r.allocation_rule_id,
    r.organization_id,
    r.allocation_rule_code,
    r.allocation_rule_name,
    r.basis,
    r.source_legal_entity_id,
    r.source_group_account_id,
    r.source_cost_center_id,
    r.valid_from,
    r.valid_to,
    r.status