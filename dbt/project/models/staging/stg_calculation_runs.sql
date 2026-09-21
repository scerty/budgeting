select
    id as calculation_run_id,
    organization_id,
    scenario_version_id,
    status,
    started_at,
    completed_at,
    input_snapshot,
    error_message,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_calculationrun') }}