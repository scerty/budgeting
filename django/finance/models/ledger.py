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
from .operations import *  # noqa: F401,F403
from .planning_rules import *  # noqa: F401,F403
from .access import *  # noqa: F401,F403
from .workflow import *  # noqa: F401,F403


class AuditLog(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="audit_logs"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="finance_audit_logs",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("content_type", "object_id")
    action = models.CharField(max_length=80)
    changes = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

class JournalEntry(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="journal_entries"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="journal_entries"
    )
    fiscal_period = models.ForeignKey(
        FiscalPeriod, on_delete=models.PROTECT, related_name="journal_entries"
    )
    entry_number = models.CharField(max_length=80)
    entry_date = models.DateField()
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="journal_entries"
    )
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=16, choices=JournalEntryStatus.choices, default=JournalEntryStatus.DRAFT
    )
    source_system = models.CharField(max_length=80, blank=True)
    source_entity = models.CharField(max_length=120, blank=True)
    source_record_id = models.CharField(max_length=160, null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="posted_journal_entries",
    )
    reversal_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reversals",
    )

    class Meta:
        ordering = ["-entry_date", "entry_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "entry_number"],
                name="uniq_journal_entry_number_entity",
            ),
            models.UniqueConstraint(
                fields=["source_system", "source_entity", "source_record_id"],
                condition=Q(source_record_id__isnull=False),
                name="uniq_journal_entry_source_record",
            ),
        ]

    def clean(self):
        if self.legal_entity.organization_id != self.organization_id:
            raise ValidationError("Journal entity must belong to the organization.")
        if self.fiscal_period.calendar_id != self.legal_entity.fiscal_calendar_id:
            raise ValidationError("Journal period must use the entity fiscal calendar.")
        if self.status == JournalEntryStatus.POSTED and not self.posted_at:
            raise ValidationError("Posted journal entries require posted_at.")

    def validate_balanced(self):
        if not self.pk:
            raise ValidationError("Journal entry must be saved before balancing.")
        lines = self.lines.all()
        if not lines.exists():
            raise ValidationError("Journal entry must have at least one line.")
        debit_total = sum(lines.values_list("debit", flat=True), Decimal("0"))
        credit_total = sum(lines.values_list("credit", flat=True), Decimal("0"))
        if debit_total == 0 or debit_total != credit_total:
            raise ValidationError("Journal entry debits and credits must balance.")

    def post(self, user=None):
        self.validate_balanced()
        self.status = JournalEntryStatus.POSTED
        self.posted_at = timezone.now()
        self.posted_by = user
        self.full_clean()
        self.save(update_fields=["status", "posted_at", "posted_by", "updated_at"])

class JournalEntryLine(TimeStampedModel):
    entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE, related_name="lines"
    )
    line_number = models.PositiveIntegerField()
    entity_account = models.ForeignKey(
        EntityAccount, on_delete=models.PROTECT, related_name="journal_lines"
    )
    group_account = models.ForeignKey(
        GroupAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="journal_lines"
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    profit_center = models.ForeignKey(
        ProfitCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    business_unit = models.ForeignKey(
        BusinessUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.PROTECT, related_name="journal_lines"
    )
    counterparty_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="counterparty_journal_lines",
    )
    description = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))

    class Meta:
        ordering = ["entry_id", "line_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["entry", "line_number"], name="uniq_journal_line_number"
            ),
            models.CheckConstraint(
                condition=(Q(debit__gt=0) & Q(credit=0))
                | (Q(debit=0) & Q(credit__gt=0)),
                name="journal_line_one_sided_amount",
            ),
        ]

    def clean(self):
        entry_entity_id = self.entry.legal_entity_id
        if self.entity_account.legal_entity_id != entry_entity_id:
            raise ValidationError("Journal local account must belong to the entry entity.")
        if self.group_account_id and self.group_account.organization_id != self.entry.organization_id:
            raise ValidationError("Journal group account must belong to the entry organization.")
        if self.branch_id and self.branch.legal_entity_id not in (None, entry_entity_id):
            raise ValidationError("Journal branch must belong to the entry entity.")
        if self.department_id:
            department_entity_id = self.department.legal_entity_id or (
                self.department.branch.legal_entity_id
                if self.department.branch_id and self.department.branch
                else None
            )
            if department_entity_id not in (None, entry_entity_id):
                raise ValidationError("Journal department must belong to the entry entity.")
        if self.cost_center_id and self.cost_center.legal_entity_id != entry_entity_id:
            raise ValidationError("Journal cost center must belong to the entry entity.")
        if self.profit_center_id and self.profit_center.legal_entity_id != entry_entity_id:
            raise ValidationError("Journal profit center must belong to the entry entity.")
        if self.project_id and self.project.legal_entity_id != entry_entity_id:
            raise ValidationError("Journal project must belong to the entry entity.")
        if self.business_unit_id and self.business_unit.organization_id != self.entry.organization_id:
            raise ValidationError("Journal business unit must belong to the entry organization.")
        if self.counterparty_entity_id:
            if self.counterparty_entity.organization_id != self.entry.organization_id:
                raise ValidationError("Counterparty must belong to the entry organization.")
            if self.counterparty_entity_id == entry_entity_id:
                raise ValidationError("Counterparty cannot equal the entry entity.")

__all__ = ['AuditLog', 'JournalEntry', 'JournalEntryLine']
