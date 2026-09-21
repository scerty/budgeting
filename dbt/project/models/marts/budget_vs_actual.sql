{{ config(materialized='table') }}

with aggregated as (

    select
        organization_id,
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
        currency_code,
        sum(case when source_kind = 'budget' then amount else 0 end) as budget_amount,
        sum(case when source_kind = 'actuals' then amount else 0 end) as actual_amount,
        sum(case when source_kind = 'actuals' then amount else 0 end)
            - sum(case when source_kind = 'budget' then amount else 0 end) as variance_amount
    from {{ ref('int_actuals_budget_ready') }}
    group by
        organization_id,
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
        currency_code

)

select
    a.*,
    o.organization_code,
    o.display_name as organization_name,
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
from aggregated as a
left join {{ ref('dim_organization') }} as o
    on a.organization_id = o.organization_id
left join {{ ref('dim_fiscal_period') }} as fp
    on a.fiscal_period_id = fp.fiscal_period_id
left join {{ ref('dim_legal_entity') }} as le
    on a.legal_entity_id = le.legal_entity_id
left join {{ ref('dim_branch') }} as b
    on a.branch_id = b.branch_id
left join {{ ref('dim_department') }} as d
    on a.department_id = d.department_id
left join {{ ref('dim_group_account') }} as ga
    on a.group_account_id = ga.group_account_id