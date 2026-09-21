{{ config(materialized='table') }}

select
    p.*,
    o.organization_code,
    o.display_name as organization_name,
    sv.scenario_version_code,
    sv.scenario_version_name,
    sv.status as scenario_version_status,
    fp.fiscal_period_code,
    fp.fiscal_period_name,
    fp.fiscal_year,
    le.entity_code as legal_entity_code,
    le.legal_name as legal_entity_name,
    b.branch_code,
    b.branch_name,
    d.department_code,
    d.department_name,
    ga.group_account_code,
    ga.group_account_name
from {{ ref('int_planning_facts_enriched') }} as p
left join {{ ref('dim_organization') }} as o
    on p.organization_id = o.organization_id
left join {{ ref('dim_scenario_version') }} as sv
    on p.scenario_version_id = sv.scenario_version_id
left join {{ ref('dim_fiscal_period') }} as fp
    on p.fiscal_period_id = fp.fiscal_period_id
left join {{ ref('dim_legal_entity') }} as le
    on p.legal_entity_id = le.legal_entity_id
left join {{ ref('dim_branch') }} as b
    on p.branch_id = b.branch_id
left join {{ ref('dim_department') }} as d
    on p.department_id = d.department_id
left join {{ ref('dim_group_account') }} as ga
    on p.group_account_id = ga.group_account_id