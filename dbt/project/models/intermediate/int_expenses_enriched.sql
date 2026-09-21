with expenses as (

    select *
    from {{ ref('stg_expenses') }}

),

departments as (

    select *
    from {{ ref('stg_departments') }}

),

branches as (

    select *
    from {{ ref('stg_branches') }}

),

legal_entities as (

    select
        legal_entity_id,
        organization_id
    from {{ ref('stg_legal_entities') }}

)

select
    e.expense_id,
    e.source_system,
    e.source_entity,
    e.source_record_id,
    e.record_hash,
    e.amount,
    e.currency_code,
    e.currency_master_id,
    e.description,
    e.expense_date,
    coalesce(e.legal_entity_id, b.legal_entity_id, d.legal_entity_id) as legal_entity_id,
    le.organization_id,
    e.entity_account_id,
    e.group_account_id,
    e.cost_center_id,
    e.profit_center_id,
    e.business_unit_id,
    e.project_id,
    e.is_deleted,
    e.ingested_at,
    e.source_created_at,
    e.source_updated_at,
    e.created_at,
    e.updated_at,

    e.department_id,
    d.department_code,
    d.department_name,
    d.legal_entity_id as department_legal_entity_id,

    coalesce(e.branch_id, d.branch_id) as branch_id,
    b.branch_code,
    b.branch_name,
    b.city

from expenses as e

left join departments as d
    on e.department_id = d.department_id

left join branches as b
    on coalesce(e.branch_id, d.branch_id) = b.branch_id

left join legal_entities as le
    on coalesce(e.legal_entity_id, b.legal_entity_id, d.legal_entity_id) = le.legal_entity_id