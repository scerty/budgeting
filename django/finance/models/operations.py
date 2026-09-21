from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .base import *  # noqa: F401,F403

from .organization import *  # noqa: F401,F403
from .planning import *  # noqa: F401,F403
from .ingestion import *  # noqa: F401,F403


class Expense(TimeStampedModel):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="expenses")
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="expenses"
    )
    legal_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    entity_account = models.ForeignKey(
        EntityAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    group_account = models.ForeignKey(
        GroupAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    profit_center = models.ForeignKey(
        ProfitCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    business_unit = models.ForeignKey(
        BusinessUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.PROTECT, related_name="expenses"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    currency_master = models.ForeignKey(
        Currency,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expenses",
    )
    expense_date = models.DateField()
    description = models.CharField(max_length=255)
    source_system = models.CharField(max_length=80, default="django")
    source_entity = models.CharField(max_length=120, default="finance_expense")
    source_record_id = models.CharField(max_length=160, null=True, blank=True)
    record_hash = models.CharField(max_length=128, blank=True)
    ingested_at = models.DateTimeField(default=timezone.now)
    source_created_at = models.DateTimeField(null=True, blank=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["expense_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "source_entity", "source_record_id"],
                condition=Q(source_record_id__isnull=False),
                name="uniq_expense_source_record",
            ),
        ]
        indexes = [
            models.Index(fields=["expense_date"]),
            models.Index(fields=["legal_entity", "expense_date"]),
            models.Index(fields=["source_system", "source_entity", "source_updated_at"]),
        ]

    def clean(self):
        if self.branch_id and self.department_id and self.department.branch_id not in (
            None,
            self.branch_id,
        ):
            raise ValidationError("Expense branch must match the department branch.")
        if self.legal_entity_id and self.branch_id and self.branch.legal_entity_id not in (
            None,
            self.legal_entity_id,
        ):
            raise ValidationError("Expense branch must belong to the legal entity.")
        if self.legal_entity_id and self.department_id:
            department_entity_id = self.department.legal_entity_id or (
                self.department.branch.legal_entity_id if self.department.branch_id else None
            )
            if department_entity_id not in (None, self.legal_entity_id):
                raise ValidationError("Expense department must belong to the legal entity.")
        if self.entity_account_id and self.legal_entity_id:
            if self.entity_account.legal_entity_id != self.legal_entity_id:
                raise ValidationError("Expense local account must belong to the legal entity.")
        if self.group_account_id and self.legal_entity_id:
            if self.group_account.organization_id != self.legal_entity.organization_id:
                raise ValidationError("Expense group account must belong to the organization.")
        if self.cost_center_id and self.legal_entity_id:
            if self.cost_center.legal_entity_id != self.legal_entity_id:
                raise ValidationError("Expense cost center must belong to the legal entity.")
        if self.project_id and self.legal_entity_id:
            if self.project.legal_entity_id != self.legal_entity_id:
                raise ValidationError("Expense project must belong to the legal entity.")
        if self.currency_master_id and self.currency.upper() != self.currency_master.code:
            raise ValidationError("Expense currency and currency master must match.")

    def __str__(self):
        return f"{self.description} - {self.amount} {self.currency}"

class ExchangeRate(TimeStampedModel):
    from_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="exchange_rates_from"
    )
    to_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="exchange_rates_to"
    )
    rate_date = models.DateField()
    rate_type = models.CharField(
        max_length=16, choices=ExchangeRateType.choices, default=ExchangeRateType.SPOT
    )
    rate = models.DecimalField(max_digits=24, decimal_places=12)
    source_system = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["-rate_date", "from_currency_id", "to_currency_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["from_currency", "to_currency", "rate_date", "rate_type"],
                name="uniq_exchange_rate_date_type",
            ),
            models.CheckConstraint(
                condition=Q(rate__gt=0), name="exchange_rate_positive"
            ),
        ]

    def clean(self):
        if self.from_currency_id and self.from_currency_id == self.to_currency_id:
            raise ValidationError("Exchange rate currencies must be different.")

class TaxCode(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="tax_codes"
    )
    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="tax_codes",
    )
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    tax_type = models.CharField(max_length=20, choices=TaxType.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_tax_code_org"
            ),
        ]

class TaxRate(TimeStampedModel):
    tax_code = models.ForeignKey(
        TaxCode, on_delete=models.CASCADE, related_name="rates"
    )
    rate = models.DecimalField(max_digits=7, decimal_places=4)
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    is_recoverable = models.BooleanField(default=False)

    class Meta:
        ordering = ["tax_code_id", "valid_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["tax_code", "valid_from"], name="uniq_tax_rate_start"
            ),
            models.CheckConstraint(
                condition=Q(rate__gte=0) & Q(rate__lte=100),
                name="tax_rate_range",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="tax_rate_valid_dates",
            ),
        ]

class Supplier(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="suppliers"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    legal_name = models.CharField(max_length=255, blank=True)
    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="suppliers",
    )
    tax_registration_number = models.CharField(max_length=100, blank=True)
    default_currency = models.ForeignKey(
        Currency,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="default_supplier_currency",
    )
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_supplier_code_org"
            ),
        ]

class Customer(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="customers"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    legal_name = models.CharField(max_length=255, blank=True)
    country = models.ForeignKey(
        Country,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="customers",
    )
    tax_registration_number = models.CharField(max_length=100, blank=True)
    default_currency = models.ForeignKey(
        Currency,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="default_customer_currency",
    )
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_customer_code_org"
            ),
        ]

class Invoice(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="invoices"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="invoices"
    )
    direction = models.CharField(max_length=16, choices=InvoiceDirection.choices)
    supplier = models.ForeignKey(
        Supplier,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    invoice_number = models.CharField(max_length=80)
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="invoices"
    )
    subtotal = models.DecimalField(max_digits=18, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    total_amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(
        max_length=16, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT
    )
    description = models.CharField(max_length=255, blank=True)
    source_system = models.CharField(max_length=80, default="django")
    source_entity = models.CharField(max_length=120, default="finance_invoice")
    source_record_id = models.CharField(max_length=160, null=True, blank=True)
    record_hash = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["-invoice_date", "invoice_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "direction", "invoice_number"],
                name="uniq_invoice_number_entity_direction",
            ),
            models.UniqueConstraint(
                fields=["source_system", "source_entity", "source_record_id"],
                condition=Q(source_record_id__isnull=False),
                name="uniq_invoice_source_record",
            ),
            models.CheckConstraint(
                condition=Q(subtotal__gte=0)
                & Q(tax_amount__gte=0)
                & Q(total_amount__gte=0),
                name="invoice_amounts_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(due_date__isnull=True) | Q(due_date__gte=F("invoice_date")),
                name="invoice_due_after_invoice",
            ),
        ]

    def clean(self):
        if self.legal_entity_id and self.organization_id:
            if self.legal_entity.organization_id != self.organization_id:
                raise ValidationError("Invoice entity must belong to the organization.")
        if self.supplier_id and self.customer_id:
            raise ValidationError("Invoice cannot have both supplier and customer.")
        if self.direction == InvoiceDirection.PAYABLE and not self.supplier_id:
            raise ValidationError("Payable invoices require a supplier.")
        if self.direction == InvoiceDirection.RECEIVABLE and not self.customer_id:
            raise ValidationError("Receivable invoices require a customer.")
        if self.supplier_id and self.supplier.organization_id != self.organization_id:
            raise ValidationError("Supplier must belong to the invoice organization.")
        if self.customer_id and self.customer.organization_id != self.organization_id:
            raise ValidationError("Customer must belong to the invoice organization.")
        if self.total_amount != self.subtotal + self.tax_amount:
            raise ValidationError("Invoice total must equal subtotal plus tax.")

    def validate_line_totals(self):
        if not self.pk:
            raise ValidationError("Invoice must be saved before validating lines.")
        line_subtotal = sum(
            self.lines.values_list("net_amount", flat=True), Decimal("0")
        )
        line_tax = sum(
            self.lines.values_list("tax_amount", flat=True), Decimal("0")
        )
        if line_subtotal != self.subtotal or line_tax != self.tax_amount:
            raise ValidationError("Invoice totals do not match invoice lines.")

class InvoiceLine(TimeStampedModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    line_number = models.PositiveIntegerField()
    description = models.CharField(max_length=255)
    entity_account = models.ForeignKey(
        EntityAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoice_lines",
    )
    group_account = models.ForeignKey(
        GroupAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoice_lines",
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="invoice_lines"
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoice_lines",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoice_lines",
    )
    profit_center = models.ForeignKey(
        ProfitCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoice_lines",
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoice_lines",
    )
    tax_code = models.ForeignKey(
        TaxCode,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoice_lines",
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("1"))
    unit_price = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    net_amount = models.DecimalField(max_digits=18, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    gross_amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        ordering = ["invoice_id", "line_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["invoice", "line_number"], name="uniq_invoice_line_number"
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0)
                & Q(unit_price__gte=0)
                & Q(net_amount__gte=0)
                & Q(tax_amount__gte=0)
                & Q(gross_amount__gte=0),
                name="invoice_line_amounts_non_negative",
            ),
        ]

    def clean(self):
        invoice_entity_id = self.invoice.legal_entity_id
        if self.entity_account_id and self.entity_account.legal_entity_id != invoice_entity_id:
            raise ValidationError("Invoice local account must belong to the invoice entity.")
        if self.group_account_id and self.group_account.organization_id != self.invoice.organization_id:
            raise ValidationError("Invoice group account must belong to the invoice organization.")
        if self.tax_code_id and self.tax_code.organization_id != self.invoice.organization_id:
            raise ValidationError("Invoice tax code must belong to the invoice organization.")
        if self.branch_id and self.branch.legal_entity_id not in (None, invoice_entity_id):
            raise ValidationError("Invoice branch must belong to the invoice entity.")
        if self.cost_center_id and self.cost_center.legal_entity_id != invoice_entity_id:
            raise ValidationError("Invoice cost center must belong to the invoice entity.")
        if self.project_id and self.project.legal_entity_id != invoice_entity_id:
            raise ValidationError("Invoice project must belong to the invoice entity.")
        if self.gross_amount != self.net_amount + self.tax_amount:
            raise ValidationError("Invoice line gross amount must equal net plus tax.")

class Payment(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="payments"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="payments"
    )
    direction = models.CharField(max_length=16, choices=InvoiceDirection.choices)
    supplier = models.ForeignKey(
        Supplier,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    customer = models.ForeignKey(
        Customer,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    payment_reference = models.CharField(max_length=100)
    payment_date = models.DateField()
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="payments"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(
        max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.DRAFT
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-payment_date", "payment_reference"]
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "payment_reference"],
                name="uniq_payment_reference_entity",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0), name="payment_amount_positive"
            ),
        ]

    def clean(self):
        if self.legal_entity_id and self.organization_id:
            if self.legal_entity.organization_id != self.organization_id:
                raise ValidationError("Payment entity must belong to the organization.")
        if self.supplier_id and self.customer_id:
            raise ValidationError("Payment cannot have both supplier and customer.")
        if self.direction == InvoiceDirection.PAYABLE and not self.supplier_id:
            raise ValidationError("Payable payments require a supplier.")
        if self.direction == InvoiceDirection.RECEIVABLE and not self.customer_id:
            raise ValidationError("Receivable payments require a customer.")

class PaymentAllocation(TimeStampedModel):
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="allocations"
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name="payment_allocations"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "invoice"], name="uniq_payment_invoice_allocation"
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0), name="payment_allocation_positive"
            ),
        ]

    def clean(self):
        if self.payment.legal_entity_id != self.invoice.legal_entity_id:
            raise ValidationError("Payment and invoice must belong to the same entity.")
        if self.payment.currency_id != self.invoice.currency_id:
            raise ValidationError("Payment and invoice currencies must match.")
        if self.payment.direction != self.invoice.direction:
            raise ValidationError("Payment and invoice directions must match.")

__all__ = ['Expense', 'ExchangeRate', 'TaxCode', 'TaxRate', 'Supplier', 'Customer', 'Invoice', 'InvoiceLine', 'Payment', 'PaymentAllocation']
