select
    budget_version_id,
    row_difference,
    amount_difference
from {{ ref('reconciliation_budget') }}
where not is_reconciled