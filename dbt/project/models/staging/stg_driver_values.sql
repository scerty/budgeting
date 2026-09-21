select
    id as driver_value_id,
    driver_id as planning_driver_id,
    scenario_version_id,
    fiscal_period_id,
    legal_entity_id,
    branch_id,
    department_id,
    project_id,
    value,
    currency_id,
    source,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_drivervalue') }}