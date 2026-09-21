select
    id as fiscal_period_id,
    calendar_id as fiscal_calendar_id,
    code as fiscal_period_code,
    name as fiscal_period_name,
    period_type,
    start_date,
    end_date,
    status,
    is_open_for_actuals,
    is_open_for_planning,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_fiscalperiod') }}