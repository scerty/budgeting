{{ config(materialized='view') }}

select
    source_system,
    source_entity,
    source_record_id,
    count(*) as duplicate_row_count,
    'duplicate_source_record' as exception_reason,
    'stg_expenses' as source_model,
    current_timestamp as discovered_at
from {{ ref('stg_expenses') }}
where source_record_id is not null
group by
    source_system,
    source_entity,
    source_record_id
having count(*) > 1