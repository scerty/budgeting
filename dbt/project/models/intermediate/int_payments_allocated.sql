with allocated as (

    select
        payment_id,
        sum(amount) as allocated_amount,
        count(*) as allocation_count
    from {{ ref('stg_payment_allocations') }}
    group by payment_id

)

select
    p.payment_id,
    p.organization_id,
    p.legal_entity_id,
    p.direction as payment_direction,
    p.supplier_id,
    p.customer_id,
    p.payment_reference,
    p.payment_date,
    p.currency_id,
    c.currency_code,
    p.amount,
    coalesce(a.allocated_amount, 0) as allocated_amount,
    p.amount - coalesce(a.allocated_amount, 0) as unallocated_amount,
    coalesce(a.allocation_count, 0) as allocation_count,
    p.status as payment_status,
    p.description,
    p.created_at,
    p.updated_at
from {{ ref('stg_payments') }} as p
left join allocated as a
    on p.payment_id = a.payment_id
left join {{ ref('stg_currencies') }} as c
    on p.currency_id = c.currency_id
where lower(p.status) in ('submitted', 'posted', 'reconciled')