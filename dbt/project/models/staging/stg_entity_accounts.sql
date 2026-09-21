select
    id as entity_account_id,
    legal_entity_id,
    code as entity_account_code,
    name as entity_account_name,
    account_type,
    normal_balance,
    parent_id as parent_entity_account_id,
    is_posting_allowed,
    is_active,
    created_at,
    updated_at
from {{ source('postgres_app', 'finance_entityaccount') }}