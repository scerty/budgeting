select
    id as scenario_version_id,
    scenario_id,
    code as scenario_version_code,
    name as scenario_version_name,
    version_number,
    status,
    based_on_id as based_on_scenario_version_id,
    is_final,
    locked_at,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_scenarioversion') }}