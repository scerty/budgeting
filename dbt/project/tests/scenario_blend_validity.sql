select
    scenario_blend_id,
    has_valid_source,
    has_valid_period_range,
    has_same_calendar,
    has_same_organization
from {{ ref('int_scenario_blends_effective') }}
where not has_valid_source
   or not has_valid_period_range
   or not has_same_calendar
   or not has_same_organization