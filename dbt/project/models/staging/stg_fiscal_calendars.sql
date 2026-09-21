select
    id as fiscal_calendar_id,
    organization_id,
    code as fiscal_calendar_code,
    name as fiscal_calendar_name,
    timezone,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_fiscalcalendar') }}