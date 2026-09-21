with components as (

    select
        b.scenario_blend_id,
        b.result_scenario_version_id,
        b.source_kind,
        b.source_scenario_version_id,
        b.fiscal_period_from_id,
        b.fiscal_period_to_id,
        p_from.start_date as period_from_date,
        p_to.end_date as period_to_date,
        p_from.fiscal_calendar_id,
        b.priority,
        b.created_at,
        b.updated_at
    from {{ ref('stg_scenario_blends') }} as b
    left join {{ ref('stg_fiscal_periods') }} as p_from
        on b.fiscal_period_from_id = p_from.fiscal_period_id
    left join {{ ref('stg_fiscal_periods') }} as p_to
        on b.fiscal_period_to_id = p_to.fiscal_period_id

)

select
    c.*,
    rv.scenario_id as result_scenario_id,
    sv.scenario_id as source_scenario_id,
    rs.organization_id as result_organization_id,
    ss.organization_id as source_organization_id,
    p_to.fiscal_calendar_id as to_fiscal_calendar_id,
    c.source_kind = 'actuals' or c.source_scenario_version_id is not null
        as has_valid_source,
    c.period_from_date <= c.period_to_date as has_valid_period_range,
    c.fiscal_calendar_id = p_to.fiscal_calendar_id as has_same_calendar,
    rs.organization_id = ss.organization_id
        or c.source_scenario_version_id is null as has_same_organization
from components as c
left join {{ ref('stg_scenario_versions') }} as rv
    on c.result_scenario_version_id = rv.scenario_version_id
left join {{ ref('stg_scenario_versions') }} as sv
    on c.source_scenario_version_id = sv.scenario_version_id
left join {{ ref('stg_scenarios') }} as rs
    on rv.scenario_id = rs.scenario_id
left join {{ ref('stg_scenarios') }} as ss
    on sv.scenario_id = ss.scenario_id
left join {{ ref('stg_fiscal_periods') }} as p_to
    on c.fiscal_period_to_id = p_to.fiscal_period_id