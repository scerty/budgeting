select
    id as allocation_rule_id,
    organization_id,
    code as allocation_rule_code,
    name as allocation_rule_name,
    basis,
    source_legal_entity_id,
    source_group_account_id,
    source_cost_center_id,
    valid_from,
    valid_to,
    status,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_allocationrule') }}