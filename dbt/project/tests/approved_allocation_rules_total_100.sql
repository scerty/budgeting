select
    allocation_rule_id,
    total_allocation_percentage,
    is_fully_allocated
from {{ ref('int_allocation_rules_effective') }}
where lower(status) = 'approved'
  and is_effective
  and not is_fully_allocated