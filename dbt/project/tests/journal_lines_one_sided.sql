select journal_line_id
from {{ ref('stg_journal_lines') }}
where (debit_amount <= 0 and credit_amount <= 0)
   or (debit_amount > 0 and credit_amount > 0)