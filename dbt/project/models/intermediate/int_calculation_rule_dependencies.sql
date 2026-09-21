select
    d.calculation_rule_dependency_id,
    d.calculation_rule_id,
    r.calculation_rule_code,
    d.depends_on_calculation_rule_id,
    depends_on.calculation_rule_code as depends_on_calculation_rule_code,
    r.organization_id,
    r.scenario_version_id,
    r.priority,
    r.valid_from,
    r.valid_to
from {{ ref('stg_calculation_rule_dependencies') }} as d
inner join {{ ref('stg_calculation_rules') }} as r
    on d.calculation_rule_id = r.calculation_rule_id
inner join {{ ref('stg_calculation_rules') }} as depends_on
    on d.depends_on_calculation_rule_id = depends_on.calculation_rule_id
where r.is_active is true