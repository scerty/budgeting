select
    id as calculation_rule_id,
    organization_id,
    code as calculation_rule_code,
    name as calculation_rule_name,
    rule_type,
    expression,
    input_keys,
    output_unit,
    priority,
    scenario_version_id,
    target_group_account_id,
    valid_from,
    valid_to,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_calculationrule') }}