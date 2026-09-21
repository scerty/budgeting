select
    calculation_run_id,
    scenario_version_id,
    fiscal_period_id,
    legal_entity_id,
    group_account_id,
    entity_account_id,
    branch_id,
    department_id,
    cost_center_id,
    profit_center_id,
    business_unit_id,
    project_id,
    count(*) as row_count
from {{ ref('fact_planning') }}
group by
    calculation_run_id,
    scenario_version_id,
    fiscal_period_id,
    legal_entity_id,
    group_account_id,
    entity_account_id,
    branch_id,
    department_id,
    cost_center_id,
    profit_center_id,
    business_unit_id,
    project_id
having count(*) > 1