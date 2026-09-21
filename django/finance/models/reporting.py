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
from .ledger import *  # noqa: F401,F403


class AccountHierarchy(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="account_hierarchies"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code", "version"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code", "version"],
                name="uniq_account_hierarchy_version",
            ),
            models.UniqueConstraint(
                fields=["organization"],
                condition=Q(is_default=True) & Q(is_active=True),
                name="uniq_active_default_account_hierarchy",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="account_hierarchy_valid_dates",
            ),
            models.CheckConstraint(
                condition=Q(version__gte=1), name="account_hierarchy_version_positive"
            ),
        ]

    def __str__(self):
        return f"{self.organization.code} / {self.name} v{self.version}"

class AccountHierarchyNode(TimeStampedModel):
    hierarchy = models.ForeignKey(
        AccountHierarchy, on_delete=models.CASCADE, related_name="nodes"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    group_account = models.ForeignKey(
        GroupAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="hierarchy_nodes",
    )
    node_code = models.CharField(max_length=80, blank=True)
    label = models.CharField(max_length=160, blank=True)
    is_subtotal = models.BooleanField(default=False)
    sign_multiplier = models.SmallIntegerField(default=1)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["hierarchy_id", "sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["hierarchy", "node_code"],
                condition=~Q(node_code=""),
                name="uniq_account_hierarchy_node_code",
            ),
            models.CheckConstraint(
                condition=Q(sign_multiplier=1) | Q(sign_multiplier=-1),
                name="account_hierarchy_sign_multiplier",
            ),
            models.CheckConstraint(
                condition=Q(parent__isnull=True) | ~Q(id=F("parent_id")),
                name="account_hierarchy_node_not_own_parent",
            ),
        ]

    def __str__(self):
        return self.label or (self.group_account and str(self.group_account)) or f"Node {self.pk}"

    def clean(self):
        if self.parent_id and self.parent.hierarchy_id != self.hierarchy_id:
            raise ValidationError("Hierarchy node parent must belong to the same hierarchy.")
        if self.group_account_id and self.group_account.organization_id != self.hierarchy.organization_id:
            raise ValidationError("Hierarchy account must belong to the hierarchy organization.")
        if self.is_subtotal and self.group_account_id:
            raise ValidationError("Subtotal nodes must not point at a group account.")
        if not self.is_subtotal and not self.group_account_id:
            raise ValidationError("Leaf nodes must point at a group account.")
        if self.is_subtotal and not self.label.strip():
            raise ValidationError("Subtotal nodes require a label.")
        if not self.is_subtotal and self.pk and self.children.exists():
            raise ValidationError("A node with children must remain a subtotal node.")

        ancestor = self.parent
        visited = set()
        while ancestor:
            if ancestor.pk in visited or ancestor.pk == self.pk:
                raise ValidationError("Account hierarchy nodes cannot contain cycles.")
            visited.add(ancestor.pk)
            ancestor = ancestor.parent

class ReportGroup(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="report_groups"
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    class Meta:
        ordering = ["organization_id", "sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"], name="uniq_report_group_name_org"
            ),
        ]

    def clean(self):
        if self.parent_id and self.parent.organization_id != self.organization_id:
            raise ValidationError("Report group parent must share an organization.")
        ancestor = self.parent
        visited = set()
        while ancestor:
            if ancestor.pk in visited or ancestor.pk == self.pk:
                raise ValidationError("Report groups cannot contain cycles.")
            visited.add(ancestor.pk)
            ancestor = ancestor.parent

class ReportTemplate(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="report_templates"
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    group = models.ForeignKey(
        ReportGroup,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="templates",
    )
    account_hierarchy = models.ForeignKey(
        AccountHierarchy, on_delete=models.PROTECT, related_name="report_templates"
    )
    default_legal_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="default_report_templates",
    )
    default_branch = models.ForeignKey(
        Branch,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="default_report_templates",
    )
    default_department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="default_report_templates",
    )
    default_cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="default_report_templates",
    )
    default_project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="default_report_templates",
    )
    is_shared = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_report_templates"
    )

    class Meta:
        ordering = ["organization_id", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"], name="uniq_report_template_name_org"
            ),
        ]

    def clean(self):
        if self.account_hierarchy_id and self.account_hierarchy.organization_id != self.organization_id:
            raise ValidationError("Report hierarchy must belong to the template organization.")
        if self.group_id and self.group.organization_id != self.organization_id:
            raise ValidationError("Report group must belong to the template organization.")
        if self.default_legal_entity_id and self.default_legal_entity.organization_id != self.organization_id:
            raise ValidationError("Default report entity must belong to the organization.")
        if self.default_branch_id:
            if self.default_branch.legal_entity.organization_id != self.organization_id:
                raise ValidationError("Default report branch must belong to the organization.")
            if self.default_legal_entity_id and self.default_branch.legal_entity_id not in (
                None,
                self.default_legal_entity_id,
            ):
                raise ValidationError("Default report branch must belong to the entity.")
        if self.default_department_id:
            department_entity_id = self.default_department.legal_entity_id or (
                self.default_department.branch.legal_entity_id
                if self.default_department.branch_id
                else None
            )
            if department_entity_id and self.default_legal_entity_id not in (
                None,
                department_entity_id,
            ):
                raise ValidationError("Default report department must belong to the entity.")
        if self.default_cost_center_id and self.default_cost_center.legal_entity.organization_id != self.organization_id:
            raise ValidationError("Default report cost center must belong to the organization.")
        if self.default_project_id:
            if self.default_project.legal_entity.organization_id != self.organization_id:
                raise ValidationError("Default report project must belong to the organization.")
            if self.default_legal_entity_id and self.default_project.legal_entity_id != self.default_legal_entity_id:
                raise ValidationError("Default report project must belong to the entity.")

class ReportColumnModel(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="report_column_models"
    )
    name = models.CharField(max_length=128)
    model_type = models.CharField(
        max_length=16,
        choices=ReportColumnModelType.choices,
        default=ReportColumnModelType.MONTHLY,
    )
    description = models.TextField(blank=True)
    is_shared = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "model_type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"], name="uniq_report_column_model_name_org"
            ),
        ]

class ReportColumnModelItem(TimeStampedModel):
    column_model = models.ForeignKey(
        ReportColumnModel, on_delete=models.CASCADE, related_name="items"
    )
    sort_order = models.PositiveIntegerField(default=0)
    label_prefix = models.CharField(max_length=64)
    data_type = models.CharField(max_length=16, choices=ReportColumnSourceType.choices)
    relative_period_offset = models.IntegerField(null=True, blank=True)
    period_from_offset = models.IntegerField(default=0)
    period_to_offset = models.IntegerField(default=0)
    scenario_version = models.ForeignKey(
        ScenarioVersion,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="report_column_model_items",
    )
    mixed_cutover_period = models.ForeignKey(
        FiscalPeriod,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="mixed_report_column_model_items",
    )
    prior_year = models.BooleanField(default=False)

    class Meta:
        ordering = ["column_model_id", "sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["column_model", "sort_order"],
                name="uniq_report_column_model_item_order",
            ),
            models.CheckConstraint(
                condition=Q(period_from_offset__lte=F("period_to_offset")),
                name="report_column_model_item_period_order",
            ),
        ]

    def clean(self):
        if self.scenario_version_id and self.scenario_version.scenario.organization_id != self.column_model.organization_id:
            raise ValidationError("Column model scenario must belong to the model organization.")
        if self.data_type == ReportColumnSourceType.ACTUALS and self.scenario_version_id:
            raise ValidationError("Actuals column items cannot have a scenario version.")
        if self.data_type == ReportColumnSourceType.MIXED and not self.mixed_cutover_period_id:
            raise ValidationError("Mixed column items require a cutover period.")

class ReportColumn(TimeStampedModel):
    template = models.ForeignKey(
        ReportTemplate, on_delete=models.CASCADE, related_name="columns"
    )
    sort_order = models.PositiveIntegerField(default=0)
    label = models.CharField(max_length=64)
    data_type = models.CharField(max_length=16, choices=ReportColumnType.choices)
    scenario_version = models.ForeignKey(
        ScenarioVersion,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="report_columns",
    )
    fiscal_period = models.ForeignKey(
        FiscalPeriod,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="report_columns",
    )
    mixed_cutover_period = models.ForeignKey(
        FiscalPeriod,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="mixed_report_columns",
    )
    variance_base_column = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="variance_base_usages",
    )
    variance_compare_column = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="variance_compare_usages",
    )
    variance_as_percentage = models.BooleanField(default=False)
    period_from_offset = models.IntegerField(default=0)
    period_to_offset = models.IntegerField(default=0)
    prior_year = models.BooleanField(default=False)

    class Meta:
        ordering = ["template_id", "sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["template", "sort_order"], name="uniq_report_column_order"
            ),
            models.CheckConstraint(
                condition=Q(period_from_offset__lte=F("period_to_offset")),
                name="report_column_period_order",
            ),
        ]

    def clean(self):
        if self.scenario_version_id and self.scenario_version.scenario.organization_id != self.template.organization_id:
            raise ValidationError("Report scenario must belong to the template organization.")
        if self.data_type == ReportColumnType.ACTUALS:
            if self.scenario_version_id or self.mixed_cutover_period_id:
                raise ValidationError("Actuals columns cannot have scenario or cutover data.")
        elif self.data_type == ReportColumnType.SCENARIO:
            if not self.scenario_version_id:
                raise ValidationError("Scenario columns require a scenario version.")
            if self.mixed_cutover_period_id:
                raise ValidationError("Scenario columns cannot have a mixed cutover period.")
        elif self.data_type == ReportColumnType.MIXED:
            if not self.scenario_version_id or not self.mixed_cutover_period_id:
                raise ValidationError("Mixed columns require a scenario version and cutover period.")
        elif self.data_type == ReportColumnType.VARIANCE:
            if not self.variance_base_column_id or not self.variance_compare_column_id:
                raise ValidationError("Variance columns require base and comparison columns.")
            if self.variance_base_column_id == self.pk or self.variance_compare_column_id == self.pk:
                raise ValidationError("A variance column cannot reference itself.")
            if self.variance_base_column.template_id != self.template_id or self.variance_compare_column.template_id != self.template_id:
                raise ValidationError("Variance columns must reference the same report template.")
            if self.scenario_version_id or self.mixed_cutover_period_id:
                raise ValidationError("Variance columns cannot have a direct scenario source.")
        if self.data_type != ReportColumnType.VARIANCE and (
            self.variance_base_column_id or self.variance_compare_column_id
        ):
            raise ValidationError("Only variance columns may reference variance columns.")

class ReportRunSnapshot(TimeStampedModel):
    template = models.ForeignKey(
        ReportTemplate, on_delete=models.PROTECT, related_name="snapshots"
    )
    legal_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="report_snapshots",
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="report_snapshots"
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="report_snapshots",
    )
    run_period = models.ForeignKey(
        FiscalPeriod,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="report_snapshots",
    )
    run_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="report_snapshots"
    )
    result_data = models.JSONField(default=dict)
    data_as_of = models.DateTimeField(default=timezone.now)
    source_hash = models.CharField(max_length=128, blank=True)

    def clean(self):
        organization_id = self.template.organization_id
        if self.legal_entity_id and self.legal_entity.organization_id != organization_id:
            raise ValidationError("Report snapshot entity must belong to the template organization.")
        if self.branch_id:
            if self.branch.legal_entity.organization_id != organization_id:
                raise ValidationError("Report snapshot branch must belong to the organization.")
            if self.legal_entity_id and self.branch.legal_entity_id not in (
                None,
                self.legal_entity_id,
            ):
                raise ValidationError("Report snapshot branch must belong to the entity.")
        if self.department_id and self.department.branch_id and self.branch_id:
            if self.department.branch_id != self.branch_id:
                raise ValidationError("Report snapshot department must belong to the branch.")

__all__ = ['AccountHierarchy', 'AccountHierarchyNode', 'ReportGroup', 'ReportTemplate', 'ReportColumnModel', 'ReportColumnModelItem', 'ReportColumn', 'ReportRunSnapshot']
