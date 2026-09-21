with ranked_mappings as (

    select
        m.account_mapping_id,
        m.mapping_version_id,
        m.entity_account_id,
        m.group_account_id,
        m.mapping_type,
        m.allocation_percentage,
        m.review_status,
        v.organization_id,
        v.mapping_version_code,
        v.valid_from,
        v.valid_to,
        row_number() over (
            partition by m.entity_account_id
            order by v.valid_from desc, m.account_mapping_id desc
        ) as mapping_priority
    from {{ ref('stg_account_mappings') }} as m
    inner join {{ ref('stg_mapping_versions') }} as v
        on m.mapping_version_id = v.mapping_version_id
    where lower(m.review_status) = 'approved'
      and lower(v.status) = 'approved'

)

select *
from ranked_mappings