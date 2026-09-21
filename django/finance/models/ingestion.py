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


class ImportSource(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="import_sources"
    )
    name = models.CharField(max_length=128)
    protocol = models.CharField(max_length=8, choices=ImportProtocol.choices)
    configuration = models.JSONField(default=dict, blank=True)
    secret_ref = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"], name="uniq_import_source_name_org"
            ),
        ]

    def __str__(self):
        return f"{self.organization.code} / {self.name}"

class IngestionRun(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="ingestion_runs"
    )
    import_source = models.ForeignKey(
        ImportSource,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ingestion_runs",
    )
    source_system = models.CharField(max_length=80)
    source_entity = models.CharField(max_length=120)
    strategy = models.CharField(max_length=16, choices=IngestionStrategy.choices)
    status = models.CharField(
        max_length=16, choices=IngestionRunStatus.choices, default=IngestionRunStatus.RUNNING
    )
    external_run_id = models.CharField(max_length=120, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    records_read = models.PositiveIntegerField(default=0)
    records_inserted = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    records_skipped = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    error_log = models.JSONField(default=list, blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="triggered_ingestion_runs",
    )

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "external_run_id"],
                condition=~Q(external_run_id=""),
                name="uniq_ingestion_external_run",
            ),
            models.CheckConstraint(
                condition=Q(finished_at__isnull=True) | Q(finished_at__gte=F("started_at")),
                name="ingestion_finished_after_started",
            ),
        ]

    def clean(self):
        if self.import_source_id and self.import_source.organization_id != self.organization_id:
            raise ValidationError("Import source must belong to the ingestion organization.")

class RawExpense(TimeStampedModel):
    ingestion_run = models.ForeignKey(
        IngestionRun, on_delete=models.PROTECT, related_name="raw_expenses"
    )
    source_system = models.CharField(max_length=80)
    source_entity = models.CharField(max_length=120)
    source_record_id = models.CharField(max_length=160)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3)
    expense_date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    source_account_code = models.CharField(max_length=80, blank=True)
    source_branch_code = models.CharField(max_length=80, blank=True)
    source_department_code = models.CharField(max_length=80, blank=True)
    source_cost_center_code = models.CharField(max_length=80, blank=True)
    source_created_at = models.DateTimeField(null=True, blank=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    ingested_at = models.DateTimeField(default=timezone.now)
    record_hash = models.CharField(max_length=128)
    is_deleted = models.BooleanField(default=False)
    source_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["expense_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "source_entity", "source_record_id"],
                name="uniq_raw_expense_source_record",
            ),
        ]
        indexes = [
            models.Index(fields=["source_system", "source_entity", "source_updated_at"]),
            models.Index(fields=["record_hash"]),
        ]

class RawJournalLine(TimeStampedModel):
    ingestion_run = models.ForeignKey(
        IngestionRun, on_delete=models.PROTECT, related_name="raw_journal_lines"
    )
    source_system = models.CharField(max_length=80)
    source_entity = models.CharField(max_length=120)
    source_record_id = models.CharField(max_length=160)
    source_line_id = models.CharField(max_length=160)
    source_legal_entity_code = models.CharField(max_length=80, blank=True)
    document_number = models.CharField(max_length=160, blank=True)
    line_number = models.PositiveIntegerField(null=True, blank=True)
    posting_date = models.DateField()
    document_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    source_account_code = models.CharField(max_length=80)
    source_branch_code = models.CharField(max_length=80, blank=True)
    source_department_code = models.CharField(max_length=80, blank=True)
    source_cost_center_code = models.CharField(max_length=80, blank=True)
    source_profit_center_code = models.CharField(max_length=80, blank=True)
    source_business_unit_code = models.CharField(max_length=80, blank=True)
    source_project_code = models.CharField(max_length=80, blank=True)
    source_counterparty_code = models.CharField(max_length=80, blank=True)
    currency = models.CharField(max_length=3)
    debit_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    credit_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    reporting_currency = models.CharField(max_length=3, blank=True)
    reporting_debit_amount = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    reporting_credit_amount = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    source_created_at = models.DateTimeField(null=True, blank=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    ingested_at = models.DateTimeField(default=timezone.now)
    record_hash = models.CharField(max_length=128)
    is_deleted = models.BooleanField(default=False)
    source_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["posting_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "source_entity", "source_record_id", "source_line_id"],
                name="uniq_raw_journal_line_source_record",
            ),
            models.CheckConstraint(
                condition=(Q(debit_amount__gt=0) & Q(credit_amount=0))
                | (Q(debit_amount=0) & Q(credit_amount__gt=0)),
                name="raw_journal_line_one_sided_amount",
            ),
        ]
        indexes = [
            models.Index(fields=["ingestion_run", "posting_date"]),
            models.Index(fields=["source_system", "source_entity", "source_updated_at"]),
            models.Index(fields=["record_hash"]),
        ]

    def clean(self):
        if self.ingestion_run_id:
            if self.source_system != self.ingestion_run.source_system:
                raise ValidationError("Raw journal line source_system must match its ingestion run.")
            if self.source_entity != self.ingestion_run.source_entity:
                raise ValidationError("Raw journal line source_entity must match its ingestion run.")

    def __str__(self):
        return f"{self.source_record_id}/{self.source_line_id} ({self.posting_date})"

class IngestionIssue(TimeStampedModel):
    ingestion_run = models.ForeignKey(
        IngestionRun, on_delete=models.PROTECT, related_name="issues"
    )
    severity = models.CharField(
        max_length=8,
        choices=IngestionIssueSeverity.choices,
        default=IngestionIssueSeverity.ERROR,
    )
    source_entity = models.CharField(max_length=120)
    source_record_id = models.CharField(max_length=160, blank=True)
    source_line_id = models.CharField(max_length=160, blank=True)
    row_number = models.PositiveIntegerField(null=True, blank=True)
    code = models.CharField(max_length=80)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_ingestion_issues",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ingestion_run", "severity"]),
            models.Index(fields=["ingestion_run", "source_record_id"]),
        ]

    def clean(self):
        if self.ingestion_run_id and self.source_entity != self.ingestion_run.source_entity:
            raise ValidationError("Issue source_entity must match its ingestion run.")

class NewCodeDiscovery(TimeStampedModel):
    ingestion_run = models.ForeignKey(
        IngestionRun, on_delete=models.PROTECT, related_name="discovered_codes"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="discovered_source_codes"
    )
    code_type = models.CharField(max_length=16, choices=DiscoveryCodeType.choices)
    code = models.CharField(max_length=80)
    name = models.CharField(max_length=160, blank=True)
    status = models.CharField(
        max_length=8, choices=DiscoveryStatus.choices, default=DiscoveryStatus.PENDING
    )
    is_auto_created = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_source_code_discoveries",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["ingestion_run", "code_type", "code"],
                name="uniq_discovered_code_per_run",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "code_type", "code"]),
            models.Index(fields=["status"]),
        ]

    def clean(self):
        if self.ingestion_run_id:
            if self.organization_id != self.ingestion_run.organization_id:
                raise ValidationError("Discovered code must belong to the ingestion organization.")

__all__ = ['ImportSource', 'IngestionRun', 'RawExpense', 'RawJournalLine', 'IngestionIssue', 'NewCodeDiscovery']
