with approved_budget as (

    select
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
        null::date as actual_date,
        b.scenario,
        'budget' as source_kind,
        b.amount
    from {{ ref('fact_budget') }} as b
    where lower(b.budget_status) in ('approved', 'closed')

), erpnext_actuals as (

    select
        le.organization_id,
        fp.fiscal_period_id,
        le.legal_entity_id,
        ga.group_account_id,
        ea.entity_account_id,
        cc.branch_id,
        cc.department_id,
        cc.cost_center_id,
        null::bigint as profit_center_id,
        null::bigint as business_unit_id,
        null::bigint as project_id,
        coalesce(j.currency_code, j.reporting_currency_code, 'USD') as currency_code,
        j.posting_date as actual_date,
        'ACTUALS' as scenario,
        'actuals' as source_kind,
        j.signed_amount as amount
    from {{ ref('fact_journal_lines') }} as j
    inner join {{ ref('dim_legal_entity') }} as le
        on le.legal_name = j.source_legal_entity_code
        or le.entity_code = j.source_legal_entity_code
    inner join {{ ref('dim_entity_account') }} as ea
        on ea.legal_entity_id = le.legal_entity_id
        and ea.entity_account_code = trim(both '-' from regexp_replace(
            upper(j.source_account_code), '[^A-Z0-9]+', '-', 'g'
        ))
    inner join {{ ref('dim_group_account') }} as ga
        on ga.organization_id = le.organization_id
        and ga.group_account_code = ea.entity_account_code
        and lower(ga.account_type) = 'operating_expense'
    left join {{ ref('dim_cost_center') }} as cc
        on cc.legal_entity_id = le.legal_entity_id
        and cc.cost_center_code = trim(both '-' from regexp_replace(
            upper(j.source_cost_center_code), '[^A-Z0-9]+', '-', 'g'
        ))
    inner join {{ ref('dim_fiscal_period') }} as fp
        on j.posting_date between fp.start_date and fp.end_date
        and fp.organization_id = le.organization_id
    where j.source_system = 'erpnext'

), demo_actuals as (

    select
        e.organization_id,
        p.fiscal_period_id,
        e.legal_entity_id,
        e.group_account_id,
        e.entity_account_id,
        e.branch_id,
        e.department_id,
        e.cost_center_id,
        e.profit_center_id,
        e.business_unit_id,
        e.project_id,
        e.currency_code,
        e.expense_date as actual_date,
        'ACTUALS' as scenario,
        'actuals' as source_kind,
        e.amount
    from {{ ref('fact_expenses') }} as e
    inner join {{ ref('dim_fiscal_period') }} as p
        on e.expense_date between p.start_date and p.end_date
        and e.organization_id = p.organization_id
        where e.source_system = 'django'
            and not exists (
                    select 1
                    from {{ ref('fact_journal_lines') }} as j
                    inner join {{ ref('dim_legal_entity') }} as le
                            on le.legal_name = j.source_legal_entity_code
                            or le.entity_code = j.source_legal_entity_code
                    where j.source_system = 'erpnext'
                        and le.organization_id = e.organization_id
            )

)

select * from approved_budget
union all
select * from erpnext_actuals
union all
select * from demo_actuals