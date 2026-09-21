select
    id as allocation_rule_line_id,
    rule_id as allocation_rule_id,
    target_legal_entity_id,
    target_branch_id,
    target_department_id,
    target_cost_center_id,
    target_profit_center_id,
    target_business_unit_id,
    target_project_id,
    allocation_percentage,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_allocationruleline') }}