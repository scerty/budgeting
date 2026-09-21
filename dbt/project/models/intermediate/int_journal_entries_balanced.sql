select
    source_system,
    source_entity,
    source_record_id,
    document_number,
    count(*) as journal_line_count,
    sum(debit_amount) as total_debit,
    sum(credit_amount) as total_credit,
    sum(debit_amount) - sum(credit_amount) as balance_difference,
    sum(debit_amount) = sum(credit_amount) as is_balanced
from {{ ref('fact_journal_lines') }}
group by
    source_system,
    source_entity,
    source_record_id,
    document_number