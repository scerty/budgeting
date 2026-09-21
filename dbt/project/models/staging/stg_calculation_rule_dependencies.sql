select
    id as calculation_rule_dependency_id,
    rule_id as calculation_rule_id,
    depends_on_id as depends_on_calculation_rule_id,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_calculationruledependency') }}