{{ config(materialized='table') }}

with approved_budget_months as (

    select
        b.budget_line_id,
        b.organization_id,
        b.fiscal_period_id,
        b.legal_entity_id,
        b.group_account_id,
        b.entity_account_id,
        b.branch_id,
        b.department_id,
        b.cost_center_id,
        b.profit_center_id,
        b.business_unit_id,
        b.project_id,
        b.currency_code,
        months.month_start::date as month_start,
        b.amount,
        row_number() over (
            partition by b.budget_line_id
            order by months.month_start
        ) as month_number,
        count(*) over (partition by b.budget_line_id) as month_count
    from {{ ref('fact_budget') }} as b
    inner join {{ ref('dim_fiscal_period') }} as fp
        on b.fiscal_period_id = fp.fiscal_period_id
    cross join lateral generate_series(
        date_trunc('month', fp.start_date),
        date_trunc('month', fp.end_date),
        interval '1 month'
    ) as months(month_start)
    where lower(b.budget_status) in ('approved', 'closed')

), approved_budget as (

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
        month_start,
        case
            when month_number = month_count then amount - coalesce(
                sum(amount / month_count) over (
                    partition by organization_id, fiscal_period_id, budget_line_id
                    order by month_start
                    rows between unbounded preceding and 1 preceding
                ),
                0::numeric
            )
            else amount / month_count
        end as budget_amount,
        0::numeric as actual_amount
    from approved_budget_months

), actuals as (

    select
        a.organization_id,
        a.fiscal_period_id,
        a.legal_entity_id,
        a.group_account_id,
        a.entity_account_id,
        a.branch_id,
        a.department_id,
        a.cost_center_id,
        a.profit_center_id,
        a.business_unit_id,
        a.project_id,
        a.currency_code,
        date_trunc('month', a.actual_date)::date as month_start,
        0::numeric as budget_amount,
        a.amount as actual_amount
    from {{ ref('int_actuals_budget_ready') }} as a
    where a.source_kind = 'actuals'
      and a.actual_date is not null

), aggregated as (

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
        month_start,
        sum(budget_amount) as budget_amount,
        sum(actual_amount) as actual_amount,
        sum(actual_amount) - sum(budget_amount) as variance_amount
    from (
        select * from approved_budget
        union all
        select * from actuals
    ) as combined
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
        currency_code,
        month_start

)

select
    a.*,
    extract(year from a.month_start)::integer * 100
        + extract(month from a.month_start)::integer as month_key,
    extract(year from a.month_start)::integer as month_year,
    to_char(a.month_start, 'Mon YYYY') as month_name,
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