select
    calculation_run_id,
    calculation_run_status,
    row_difference,
    amount_difference
from {{ ref('reconciliation_planning') }}
where not is_reconciled