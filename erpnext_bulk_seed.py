from datetime import date, timedelta

import frappe
from frappe.utils import flt


COMPANY = "Finance Demo (Demo)"
ITEM_CODE = "FINANCE-BULK-SERVICE"
STRUCTURE_BRANCHES = {
    "AMM": "Amman",
    "IRB": "Irbid",
    "AQB": "Aqaba",
}


def _marker(batch, kind, index):
    return f"Finance Stack bulk demo | {batch} | {kind}-{index:04d}"


def _existing(doctype, marker):
    return frappe.db.get_value(doctype, {"remarks": marker}, "name")


def _existing_payment(marker):
    return frappe.db.get_value("Payment Entry", {"reference_no": marker}, "name")


def _get_setup():
    company = frappe.get_doc("Company", COMPANY)
    bank_account = frappe.get_all(
        "Account",
        filters={"company": COMPANY, "account_type": "Bank", "is_group": 0},
        pluck="name",
        limit=1,
    )
    warehouses = frappe.get_all(
        "Warehouse",
        filters={"company": COMPANY, "is_group": 0},
        pluck="name",
        order_by="name asc",
        limit=1,
    )
    customers = frappe.get_all(
        "Customer", filters={"disabled": 0}, pluck="name", order_by="name asc"
    )
    suppliers = frappe.get_all(
        "Supplier", filters={"disabled": 0}, pluck="name", order_by="name asc"
    )
    item_groups = frappe.get_all(
        "Item Group",
        filters={"name": "Services", "is_group": 0},
        pluck="name",
        limit=1,
    )
    if not bank_account or not warehouses or not customers or not suppliers or not item_groups:
        frappe.throw("ERPNext demo master data is incomplete for bulk seeding.")
    return {
        "company": company,
        "bank_account": bank_account[0],
        "warehouse": warehouses[0],
        "customers": customers,
        "suppliers": suppliers,
        "item_group": item_groups[0],
        "receivable": company.default_receivable_account,
        "payable": company.default_payable_account,
        "income": company.default_income_account,
        "expense": company.default_expense_account,
    }


def _ensure_item(setup):
    if frappe.db.exists("Item", ITEM_CODE):
        return ITEM_CODE
    item = frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": ITEM_CODE,
            "item_name": "Finance Stack Bulk Service",
            "item_group": setup["item_group"],
            "stock_uom": "Nos",
            "is_stock_item": 0,
            "is_sales_item": 1,
            "is_purchase_item": 1,
            "description": "Non-stock service used by the Finance Stack bulk demo seeder.",
            "item_defaults": [
                {
                    "company": COMPANY,
                    "default_warehouse": setup["warehouse"],
                    "income_account": setup["income"],
                    "expense_account": setup["expense"],
                }
            ],
        }
    )
    item.insert(ignore_permissions=True)
    frappe.db.commit()
    return item.name


def _posting_date(index):
    return date(2026, 1, 1) + timedelta(days=(index - 1) % 264)


def _create_sales_invoice(setup, item_code, batch, index):
    marker = _marker(batch, "sales", index)
    existing = _existing("Sales Invoice", marker)
    if existing:
        return existing, False
    posting_date = _posting_date(index)
    amount = flt(500 + ((index * 137) % 24500), 2)
    invoice = frappe.get_doc(
        {
            "doctype": "Sales Invoice",
            "company": COMPANY,
            "customer": setup["customers"][index % len(setup["customers"])],
            "posting_date": posting_date,
            "due_date": posting_date,
            "debit_to": setup["receivable"],
            "set_posting_time": 1,
            "remarks": marker,
            "items": [
                {
                    "item_code": item_code,
                    "qty": 1,
                    "rate": amount,
                    "income_account": setup["income"],
                }
            ],
        }
    )
    invoice.insert(ignore_permissions=True)
    invoice.submit()
    frappe.db.commit()
    return invoice.name, True


def _create_purchase_invoice(setup, item_code, batch, index):
    marker = _marker(batch, "purchase", index)
    existing = _existing("Purchase Invoice", marker)
    if existing:
        return existing, False
    posting_date = _posting_date(index + 17)
    amount = flt(700 + ((index * 211) % 30000), 2)
    invoice = frappe.get_doc(
        {
            "doctype": "Purchase Invoice",
            "company": COMPANY,
            "supplier": setup["suppliers"][index % len(setup["suppliers"])],
            "posting_date": posting_date,
            "due_date": posting_date,
            "credit_to": setup["payable"],
            "set_posting_time": 1,
            "remarks": marker,
            "items": [
                {
                    "item_code": item_code,
                    "qty": 1,
                    "rate": amount,
                    "expense_account": setup["expense"],
                }
            ],
        }
    )
    invoice.insert(ignore_permissions=True)
    invoice.submit()
    frappe.db.commit()
    return invoice.name, True


def _create_payment(setup, batch, index, invoice_name, payment_type):
    marker = _marker(batch, "payment", index)
    existing = _existing_payment(marker)
    if existing:
        return existing, False
    is_receive = payment_type == "Receive"
    invoice = frappe.get_doc(
        "Sales Invoice" if is_receive else "Purchase Invoice", invoice_name
    )
    amount = flt(invoice.grand_total, 2)
    party = invoice.customer if is_receive else invoice.supplier
    party_type = "Customer" if is_receive else "Supplier"
    party_account = setup["receivable"] if is_receive else setup["payable"]
    payment = frappe.get_doc(
        {
            "doctype": "Payment Entry",
            "payment_type": payment_type,
            "party_type": party_type,
            "party": party,
            "company": COMPANY,
            "posting_date": invoice.posting_date,
            "paid_from": party_account if is_receive else setup["bank_account"],
            "paid_to": setup["bank_account"] if is_receive else party_account,
            "paid_amount": amount,
            "received_amount": amount,
            "reference_no": marker,
            "reference_date": invoice.posting_date,
            "remarks": marker,
            "references": [
                {
                    "reference_doctype": invoice.doctype,
                    "reference_name": invoice.name,
                    "allocated_amount": amount,
                }
            ],
        }
    )
    payment.insert(ignore_permissions=True)
    payment.submit()
    frappe.db.commit()
    return payment.name, True


def run(sales_count=100, purchase_count=100, payment_count=None, batch="2026-09"):
    sales_count = int(sales_count)
    purchase_count = int(purchase_count)
    payment_count = sales_count + purchase_count if payment_count is None else int(payment_count)
    if min(sales_count, purchase_count, payment_count) < 0:
        frappe.throw("Bulk counts must not be negative.")

    setup = _get_setup()
    item_code = _ensure_item(setup)
    sales = []
    purchases = []
    created = {"sales_invoices": 0, "purchase_invoices": 0, "payment_entries": 0}

    for index in range(1, sales_count + 1):
        name, was_created = _create_sales_invoice(setup, item_code, batch, index)
        sales.append(name)
        created["sales_invoices"] += int(was_created)
    for index in range(1, purchase_count + 1):
        name, was_created = _create_purchase_invoice(setup, item_code, batch, index)
        purchases.append(name)
        created["purchase_invoices"] += int(was_created)

    targets = [(name, "Receive") for name in sales] + [(name, "Pay") for name in purchases]
    if payment_count > len(targets):
        frappe.throw("payment_count cannot exceed the number of generated invoices.")
    for index, (invoice_name, payment_type) in enumerate(targets[:payment_count], start=1):
        _, was_created = _create_payment(setup, batch, index, invoice_name, payment_type)
        created["payment_entries"] += int(was_created)

    return {
        "batch": batch,
        "item_code": item_code,
        "requested": {
            "sales_invoices": sales_count,
            "purchase_invoices": purchase_count,
            "payment_entries": payment_count,
        },
        "created": created,
    }


def run_structure(company=COMPANY):
    """Create realistic organizational master data for the demo company."""
    if not frappe.db.exists("Company", company):
        frappe.throw(f"Unknown company: {company}")

    created_branches = []
    for branch_name in STRUCTURE_BRANCHES:
        if not frappe.db.exists("Branch", branch_name):
            frappe.get_doc({"doctype": "Branch", "branch": branch_name}).insert(
                ignore_permissions=True
            )
            created_branches.append(branch_name)

    root = frappe.db.get_value(
        "Cost Center",
        {"company": company, "is_group": 1, "parent_cost_center": ["is", "not set"]},
        "name",
    )
    if not root:
        frappe.throw(f"No root Cost Center found for {company}")

    created_cost_centers = []
    for branch_name in STRUCTURE_BRANCHES:
        if frappe.db.exists(
            "Cost Center",
            {"company": company, "cost_center_name": branch_name},
        ):
            continue
        frappe.get_doc(
            {
                "doctype": "Cost Center",
                "cost_center_name": branch_name,
                "parent_cost_center": root,
                "company": company,
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)
        created_cost_centers.append(branch_name)

    frappe.db.commit()
    return {
        "company": company,
        "branches_created": created_branches,
        "cost_centers_created": created_cost_centers,
    }