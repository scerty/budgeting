select
    i.invoice_id,
    l.invoice_line_id,
    i.organization_id,
    i.legal_entity_id,
    i.direction as invoice_direction,
    i.supplier_id,
    i.customer_id,
    i.invoice_number,
    i.invoice_date,
    i.due_date,
    i.currency_id,
    c.currency_code,
    i.status as invoice_status,
    l.line_number,
    l.description as line_description,
    l.entity_account_id,
    l.group_account_id,
    l.branch_id,
    l.department_id,
    l.cost_center_id,
    l.profit_center_id,
    l.project_id,
    l.tax_code_id,
    l.quantity,
    l.unit_price,
    l.net_amount,
    l.tax_amount,
    l.gross_amount,
    i.source_system,
    i.source_entity,
    i.source_record_id,
    i.record_hash,
    i.created_at,
    i.updated_at
from {{ ref('stg_invoices') }} as i
inner join {{ ref('stg_invoice_lines') }} as l
    on i.invoice_id = l.invoice_id
left join {{ ref('stg_currencies') }} as c
    on i.currency_id = c.currency_id
where lower(i.status) in ('submitted', 'approved', 'posted', 'paid')