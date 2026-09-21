with direct_scope as (

    select
        department_id,
        legal_entity_id,
        branch_id,
        null::date as valid_from,
        null::date as valid_to,
        'department_master' as scope_source
    from {{ ref('stg_departments') }}

), entity_scope as (

    select
        department_id,
        legal_entity_id,
        null::bigint as branch_id,
        valid_from,
        valid_to,
        'entity_assignment' as scope_source
    from {{ ref('stg_department_entity_assignments') }}

), branch_scope as (

    select
        department_id,
        null::bigint as legal_entity_id,
        branch_id,
        valid_from,
        valid_to,
        'branch_assignment' as scope_source
    from {{ ref('stg_department_branch_assignments') }}

)

select distinct
    department_id,
    legal_entity_id,
    branch_id,
    valid_from,
    valid_to,
    scope_source,
    valid_from is null
        or (valid_from <= current_date and (valid_to is null or valid_to >= current_date))
        as is_effective
from (
    select * from direct_scope
    union all
    select * from entity_scope
    union all
    select * from branch_scope
) as scopes