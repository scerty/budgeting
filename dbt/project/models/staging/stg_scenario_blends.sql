select
    id as scenario_blend_id,
    result_version_id as result_scenario_version_id,
    source_kind,
    source_version_id as source_scenario_version_id,
    fiscal_period_from_id,
    fiscal_period_to_id,
    priority,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_scenarioblend') }}