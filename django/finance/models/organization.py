from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .base import *  # noqa: F401,F403


class Country(TimeStampedModel):
    iso_code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=120)
    default_currency = models.ForeignKey(
        "Currency",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="countries",
    )
    tax_jurisdiction_code = models.CharField(max_length=40, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")

    class Meta:
        ordering = ["iso_code"]

    def __str__(self):
        return f"{self.iso_code} - {self.name}"

class Currency(TimeStampedModel):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=80)
    symbol = models.CharField(max_length=8, blank=True)
    decimal_places = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.CheckConstraint(
                condition=Q(decimal_places__gte=0) & Q(decimal_places__lte=4),
                name="currency_decimal_places_range",
            ),
        ]

    def clean(self):
        self.code = self.code.upper()

    def __str__(self):
        return self.code

class FiscalCalendar(TimeStampedModel):
    organization = models.ForeignKey(
        "Organization", on_delete=models.CASCADE, related_name="fiscal_calendars"
    )
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    timezone = models.CharField(max_length=64, default="UTC")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"],
                name="uniq_fiscal_calendar_code_org",
            ),
        ]

    def __str__(self):
        return f"{self.organization.code} / {self.code}"

class Organization(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    legal_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    default_reporting_currency = models.ForeignKey(
        Currency,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reporting_organizations",
    )
    default_fiscal_calendar = models.ForeignKey(
        FiscalCalendar,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="default_for_organizations",
    )
    timezone = models.CharField(max_length=64, default="UTC")
    status = models.CharField(
        max_length=16, choices=LifecycleStatus.choices, default=LifecycleStatus.ACTIVE
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.display_name

class FiscalPeriod(TimeStampedModel):
    class PeriodType(models.TextChoices):
        MONTH = "month", "Month"
        QUARTER = "quarter", "Quarter"
        YEAR = "year", "Year"

    class PeriodStatus(models.TextChoices):
        OPEN = "open", "Open"
        SOFT_CLOSED = "soft_closed", "Soft closed"
        CLOSED = "closed", "Closed"

    calendar = models.ForeignKey(
        FiscalCalendar, on_delete=models.CASCADE, related_name="periods"
    )
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    period_type = models.CharField(max_length=16, choices=PeriodType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=16, choices=PeriodStatus.choices, default=PeriodStatus.OPEN
    )
    is_open_for_actuals = models.BooleanField(default=True)
    is_open_for_planning = models.BooleanField(default=True)

    class Meta:
        ordering = ["start_date", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["calendar", "code"], name="uniq_fiscal_period_code_calendar"
            ),
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="fiscal_period_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.calendar.code} / {self.code}"

class LegalEntity(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="legal_entities"
    )
    code = models.CharField(max_length=50)
    legal_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=120, blank=True)
    country = models.ForeignKey(
        Country, null=True, blank=True, on_delete=models.PROTECT, related_name="legal_entities"
    )
    tax_registration_number = models.CharField(max_length=100, blank=True)
    functional_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="functional_entities"
    )
    reporting_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="reporting_entities"
    )
    fiscal_calendar = models.ForeignKey(
        FiscalCalendar, on_delete=models.PROTECT, related_name="legal_entities"
    )
    parent_entity = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="child_entities",
    )
    consolidation_method = models.CharField(
        max_length=20,
        choices=ConsolidationMethod.choices,
        default=ConsolidationMethod.FULL,
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=LifecycleStatus.choices, default=LifecycleStatus.ACTIVE
    )

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_legal_entity_code_org"
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="legal_entity_valid_dates",
            ),
            models.CheckConstraint(
                condition=~Q(id=F("parent_entity_id")),
                name="legal_entity_not_own_parent",
            ),
        ]

    def clean(self):
        if self.parent_entity_id and self.parent_entity:
            if self.parent_entity.organization_id != self.organization_id:
                raise ValidationError("Parent entity must belong to the same organization.")

    def __str__(self):
        return f"{self.code} - {self.legal_name}"

class OwnershipPeriod(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="ownership_periods"
    )
    parent_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="ownership_interests"
    )
    child_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="ownership_records"
    )
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    control_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    consolidation_method = models.CharField(
        max_length=20, choices=ConsolidationMethod.choices
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["child_entity_id", "valid_from"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(ownership_percentage__gte=0) & Q(ownership_percentage__lte=100)),
                name="ownership_percentage_range",
            ),
            models.CheckConstraint(
                condition=Q(control_percentage__isnull=True)
                | (Q(control_percentage__gte=0) & Q(control_percentage__lte=100)),
                name="control_percentage_range",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="ownership_valid_dates",
            ),
            models.CheckConstraint(
                condition=~Q(parent_entity=F("child_entity")),
                name="ownership_entities_distinct",
            ),
        ]

    def clean(self):
        if self.parent_entity_id and self.child_entity_id:
            if self.parent_entity.organization_id != self.organization_id:
                raise ValidationError("Parent entity must belong to the organization.")
            if self.child_entity.organization_id != self.organization_id:
                raise ValidationError("Child entity must belong to the organization.")

class BusinessUnit(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="business_units"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_business_units",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_business_unit_code_org"
            ),
            models.CheckConstraint(
                condition=Q(parent__isnull=True) | ~Q(id=F("parent_id")),
                name="business_unit_not_own_parent",
            ),
        ]

    def clean(self):
        if self.parent_id and self.parent and self.parent.organization_id != self.organization_id:
            raise ValidationError("Parent business unit must belong to the same organization.")

class EntityBusinessUnitAssignment(TimeStampedModel):
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.CASCADE, related_name="business_unit_assignments"
    )
    business_unit = models.ForeignKey(
        BusinessUnit, on_delete=models.CASCADE, related_name="entity_assignments"
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "business_unit", "valid_from"],
                name="uniq_entity_business_unit_start",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="entity_business_unit_valid_dates",
            ),
        ]

    def clean(self):
        if self.legal_entity_id and self.business_unit_id:
            if self.legal_entity.organization_id != self.business_unit.organization_id:
                raise ValidationError("Entity and business unit must share an organization.")

class Branch(TimeStampedModel):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    legal_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="branches",
    )
    country = models.ForeignKey(
        Country, null=True, blank=True, on_delete=models.PROTECT, related_name="branches"
    )
    address = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "code"],
                condition=Q(legal_entity__isnull=False),
                name="uniq_branch_code_entity",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

class Department(TimeStampedModel):
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    branch = models.ForeignKey(
        Branch,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="departments",
    )
    legal_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="departments",
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="managed_departments",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "code"],
                condition=Q(branch__isnull=False),
                name="uniq_department_code_branch",
            ),
            models.UniqueConstraint(
                fields=["legal_entity", "code"],
                condition=Q(branch__isnull=True, legal_entity__isnull=False),
                name="uniq_department_code_entity",
            ),
            models.CheckConstraint(
                condition=Q(branch__isnull=False) | Q(legal_entity__isnull=False),
                name="department_has_scope",
            ),
        ]

    def clean(self):
        if self.branch_id and self.branch and self.legal_entity_id:
            if self.branch.legal_entity_id not in (None, self.legal_entity_id):
                raise ValidationError("Department branch and entity must match.")
        if self.parent_id and self.parent and self.parent_id == self.pk:
            raise ValidationError("Department cannot be its own parent.")

    def __str__(self):
        scope = self.branch.code if self.branch_id else self.legal_entity.code
        return f"{scope} / {self.name}"

class DepartmentEntityAssignment(TimeStampedModel):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="entity_assignments"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.CASCADE, related_name="department_assignments"
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["department", "legal_entity", "valid_from"],
                name="uniq_department_entity_start",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="department_entity_valid_dates",
            ),
        ]

class DepartmentBranchAssignment(TimeStampedModel):
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="branch_assignments"
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="department_assignments"
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["department", "branch", "valid_from"],
                name="uniq_department_branch_start",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="department_branch_valid_dates",
            ),
        ]

class CostCenter(TimeStampedModel):
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.CASCADE, related_name="cost_centers"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="cost_centers"
    )
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.PROTECT, related_name="cost_centers"
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="managed_cost_centers",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["legal_entity_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "code"], name="uniq_cost_center_code_entity"
            ),
        ]

    def clean(self):
        if self.branch_id and self.branch and self.branch.legal_entity_id not in (
            None,
            self.legal_entity_id,
        ):
            raise ValidationError("Cost center branch must belong to its legal entity.")
        if self.department_id and self.department and self.department.legal_entity_id not in (
            None,
            self.legal_entity_id,
        ):
            raise ValidationError("Cost center department must belong to its legal entity.")

class ProfitCenter(TimeStampedModel):
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.CASCADE, related_name="profit_centers"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=120)
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="profit_centers"
    )
    business_unit = models.ForeignKey(
        BusinessUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="profit_centers",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["legal_entity_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "code"], name="uniq_profit_center_code_entity"
            ),
        ]

class Project(TimeStampedModel):
    class ProjectStatus(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.CASCADE, related_name="projects"
    )
    business_unit = models.ForeignKey(
        BusinessUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=ProjectStatus.choices, default=ProjectStatus.PLANNED
    )

    class Meta:
        ordering = ["legal_entity_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "code"], name="uniq_project_code_entity"
            ),
            models.CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(start_date__isnull=True) | Q(end_date__gte=F("start_date")),
                name="project_end_after_start",
            ),
        ]

class GroupAccount(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="group_accounts"
    )
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=160)
    localized_name = models.CharField(max_length=160, blank=True)
    account_type = models.CharField(max_length=24, choices=AccountType.choices)
    normal_balance = models.CharField(max_length=8, choices=NormalBalance.choices)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    level = models.PositiveSmallIntegerField(default=1)
    is_posting_allowed = models.BooleanField(default=True)
    is_control_account = models.BooleanField(default=False)
    requires_cost_center = models.BooleanField(default=False)
    requires_project = models.BooleanField(default=False)
    requires_intercompany = models.BooleanField(default=False)
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_group_account_code_org"
            ),
            models.CheckConstraint(
                condition=Q(level__gte=1), name="group_account_level_positive"
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="group_account_valid_dates",
            ),
        ]

    def clean(self):
        if self.parent_id and self.parent and self.parent.organization_id != self.organization_id:
            raise ValidationError("Parent account must belong to the same organization.")

    def __str__(self):
        return f"{self.code} - {self.name}"

class EntityAccount(TimeStampedModel):
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.CASCADE, related_name="entity_accounts"
    )
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=160)
    account_type = models.CharField(max_length=24, choices=AccountType.choices)
    normal_balance = models.CharField(max_length=8, choices=NormalBalance.choices)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    is_posting_allowed = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["legal_entity_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "code"], name="uniq_entity_account_code"
            ),
        ]

    def clean(self):
        if self.parent_id and self.parent and self.parent.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Parent account must belong to the same legal entity.")

class MappingVersion(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="mapping_versions"
    )
    code = models.CharField(max_length=40)
    name = models.CharField(max_length=120)
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )

    class Meta:
        ordering = ["organization_id", "valid_from", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_mapping_version_code_org"
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="mapping_version_valid_dates",
            ),
        ]

class AccountMapping(TimeStampedModel):
    mapping_version = models.ForeignKey(
        MappingVersion, on_delete=models.PROTECT, related_name="account_mappings"
    )
    entity_account = models.ForeignKey(
        EntityAccount, on_delete=models.PROTECT, related_name="group_mappings"
    )
    group_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="local_mappings"
    )
    mapping_type = models.CharField(max_length=24, choices=MappingType.choices)
    allocation_percentage = models.DecimalField(
        max_digits=7, decimal_places=4, null=True, blank=True
    )
    review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_account_mappings",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["entity_account_id", "group_account_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["mapping_version", "entity_account", "group_account"],
                name="uniq_account_mapping_rule",
            ),
            models.CheckConstraint(
                condition=Q(allocation_percentage__isnull=True)
                | (Q(allocation_percentage__gte=0) & Q(allocation_percentage__lte=100)),
                name="account_mapping_allocation_range",
            ),
        ]

    def clean(self):
        if not (self.mapping_version_id and self.entity_account_id and self.group_account_id):
            return
        if self.entity_account.legal_entity.organization_id != self.mapping_version.organization_id:
            raise ValidationError("Entity account and mapping version must share an organization.")
        if self.group_account.organization_id != self.mapping_version.organization_id:
            raise ValidationError("Group account and mapping version must share an organization.")
        if self.mapping_type == MappingType.ONE_TO_MANY and self.allocation_percentage is None:
            raise ValidationError("One-to-many mappings require an allocation percentage.")

__all__ = ['Country', 'Currency', 'FiscalCalendar', 'Organization', 'FiscalPeriod', 'LegalEntity', 'OwnershipPeriod', 'BusinessUnit', 'EntityBusinessUnitAssignment', 'Branch', 'Department', 'DepartmentEntityAssignment', 'DepartmentBranchAssignment', 'CostCenter', 'ProfitCenter', 'Project', 'GroupAccount', 'EntityAccount', 'MappingVersion', 'AccountMapping']
