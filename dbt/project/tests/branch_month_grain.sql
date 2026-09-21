select
    branch_id,
    month_key,
    count(*) as row_count
from {{ ref('expenses_by_branch_month') }}
group by
    branch_id,
    month_key
having count(*) > 1
