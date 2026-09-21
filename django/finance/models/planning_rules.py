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


class PlanningAssumption(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="planning_assumptions"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    value_type = models.CharField(max_length=16, choices=PlanningValueType.choices)
    numeric_value = models.DecimalField(
        max_digits=18, decimal_places=6, null=True, blank=True
    )
    text_value = models.TextField(null=True, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    currency = models.ForeignKey(
        Currency,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_assumptions",
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code", "valid_from"],
                name="uniq_planning_assumption_start",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="planning_assumption_valid_dates",
            ),
        ]

    def clean(self):
        if self.value_type == PlanningValueType.TEXT:
            if not self.text_value:
                raise ValidationError("Text assumptions require text_value.")
        elif self.numeric_value is None:
            raise ValidationError("Numeric assumptions require numeric_value.")
        if self.currency_id and self.currency.code and self.value_type != PlanningValueType.CURRENCY:
            raise ValidationError("Currency is only valid for currency assumptions.")

class PlanningDriver(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="planning_drivers"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    unit = models.CharField(max_length=40)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_planning_drivers",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_planning_driver_code_org"
            ),
        ]

class DriverValue(TimeStampedModel):
    driver = models.ForeignKey(
        PlanningDriver, on_delete=models.CASCADE, related_name="values"
    )
    scenario_version = models.ForeignKey(
        ScenarioVersion,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="driver_values",
    )
    fiscal_period = models.ForeignKey(
        FiscalPeriod, on_delete=models.PROTECT, related_name="driver_values"
    )
    legal_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="driver_values",
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="driver_values"
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="driver_values",
    )
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.PROTECT, related_name="driver_values"
    )
    value = models.DecimalField(max_digits=18, decimal_places=6)
    currency = models.ForeignKey(
        Currency,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="driver_values",
    )
    source = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["fiscal_period_id", "driver_id"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "driver",
                    "scenario_version",
                    "fiscal_period",
                    "legal_entity",
                    "branch",
                    "department",
                    "project",
                ],
                nulls_distinct=False,
                name="uniq_driver_value_scenario_scope",
            ),
        ]

    def clean(self):
        driver_org_id = self.driver.organization_id
        if self.fiscal_period.calendar.organization_id != driver_org_id:
            raise ValidationError("Driver period must belong to the driver organization.")
        if self.scenario_version_id and self.scenario_version.scenario.organization_id != driver_org_id:
            raise ValidationError("Driver scenario must belong to the driver organization.")
        if self.legal_entity_id and self.legal_entity.organization_id != driver_org_id:
            raise ValidationError("Driver entity must belong to the driver organization.")
        if self.legal_entity_id and self.branch_id and self.branch.legal_entity_id not in (
            None,
            self.legal_entity_id,
        ):
            raise ValidationError("Driver branch must belong to the driver entity.")

class CalculationRule(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="calculation_rules"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    rule_type = models.CharField(
        max_length=24,
        choices=CalculationRuleType.choices,
        default=CalculationRuleType.DRIVER,
    )
    expression = models.TextField()
    input_keys = models.JSONField(default=list, blank=True)
    output_unit = models.CharField(max_length=40, blank=True)
    priority = models.PositiveIntegerField(default=0)
    scenario_version = models.ForeignKey(
        ScenarioVersion,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="calculation_rules",
    )
    target_group_account = models.ForeignKey(
        GroupAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="calculation_rules",
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code", "valid_from"],
                name="uniq_calculation_rule_start",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="calculation_rule_valid_dates",
            ),
        ]

    def clean(self):
        if self.target_group_account_id and self.target_group_account.organization_id != self.organization_id:
            raise ValidationError("Calculation account must belong to the organization.")
        if self.scenario_version_id and self.scenario_version.scenario.organization_id != self.organization_id:
            raise ValidationError("Calculation scenario must belong to the organization.")

class CalculationRuleDependency(TimeStampedModel):
    rule = models.ForeignKey(
        CalculationRule, on_delete=models.CASCADE, related_name="dependencies"
    )
    depends_on = models.ForeignKey(
        CalculationRule, on_delete=models.PROTECT, related_name="dependent_rules"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["rule", "depends_on"], name="uniq_calculation_rule_dependency"
            ),
            models.CheckConstraint(
                condition=~Q(rule=models.F("depends_on")),
                name="calculation_rule_dependency_not_self",
            ),
        ]

    def clean(self):
        if self.rule_id and self.depends_on_id:
            if self.rule.organization_id != self.depends_on.organization_id:
                raise ValidationError("Calculation dependencies must share an organization.")
            if self.rule.scenario_version_id and self.depends_on.scenario_version_id:
                if self.rule.scenario_version_id != self.depends_on.scenario_version_id:
                    raise ValidationError("Scenario-scoped rules must share a scenario version.")

class AllocationRule(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="allocation_rules"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    basis = models.CharField(max_length=16, choices=AllocationBasis.choices)
    source_legal_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="source_allocation_rules",
    )
    source_group_account = models.ForeignKey(
        GroupAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="source_allocation_rules",
    )
    source_cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="source_allocation_rules",
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=AllocationRuleStatus.choices,
        default=AllocationRuleStatus.DRAFT,
    )

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code", "valid_from"],
                name="uniq_allocation_rule_start",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="allocation_rule_valid_dates",
            ),
        ]

    def clean(self):
        if self.source_legal_entity_id and self.source_legal_entity.organization_id != self.organization_id:
            raise ValidationError("Allocation source entity must belong to the organization.")
        if self.source_group_account_id and self.source_group_account.organization_id != self.organization_id:
            raise ValidationError("Allocation source account must belong to the organization.")
        if self.source_cost_center_id and self.source_cost_center.legal_entity.organization_id != self.organization_id:
            raise ValidationError("Allocation source cost center must belong to the organization.")

    def validate_percentages(self):
        total = sum(
            self.lines.values_list("allocation_percentage", flat=True), Decimal("0")
        )
        if total != Decimal("100"):
            raise ValidationError("Allocation rule lines must total 100 percent.")

class AllocationRuleLine(TimeStampedModel):
    rule = models.ForeignKey(
        AllocationRule, on_delete=models.CASCADE, related_name="lines"
    )
    target_legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="allocation_rule_lines"
    )
    target_branch = models.ForeignKey(
        Branch,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="allocation_rule_lines",
    )
    target_department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="allocation_rule_lines",
    )
    target_cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="allocation_rule_lines",
    )
    target_profit_center = models.ForeignKey(
        ProfitCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="allocation_rule_lines",
    )
    target_business_unit = models.ForeignKey(
        BusinessUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="allocation_rule_lines",
    )
    target_project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="allocation_rule_lines",
    )
    allocation_percentage = models.DecimalField(max_digits=7, decimal_places=4)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "rule",
                    "target_legal_entity",
                    "target_branch",
                    "target_department",
                    "target_cost_center",
                    "target_profit_center",
                    "target_business_unit",
                    "target_project",
                ],
                nulls_distinct=False,
                name="uniq_allocation_rule_target",
            ),
            models.CheckConstraint(
                condition=(Q(allocation_percentage__gte=0) & Q(allocation_percentage__lte=100)),
                name="allocation_percentage_range",
            ),
        ]

    def clean(self):
        organization_id = self.rule.organization_id
        if self.target_legal_entity.organization_id != organization_id:
            raise ValidationError("Allocation target entity must belong to the rule organization.")
        if self.target_branch_id and self.target_branch.legal_entity_id not in (
            None,
            self.target_legal_entity_id,
        ):
            raise ValidationError("Allocation target branch must belong to the target entity.")
        if self.target_cost_center_id and self.target_cost_center.legal_entity_id != self.target_legal_entity_id:
            raise ValidationError("Allocation target cost center must belong to the target entity.")
        if self.target_project_id and self.target_project.legal_entity_id != self.target_legal_entity_id:
            raise ValidationError("Allocation target project must belong to the target entity.")
        if self.target_business_unit_id and self.target_business_unit.organization_id != organization_id:
            raise ValidationError("Allocation target business unit must belong to the rule organization.")

class CalculationRun(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="calculation_runs"
    )
    scenario_version = models.ForeignKey(
        ScenarioVersion, on_delete=models.PROTECT, related_name="calculation_runs"
    )
    status = models.CharField(
        max_length=16,
        choices=CalculationRunStatus.choices,
        default=CalculationRunStatus.RUNNING,
    )
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="planning_calculation_runs",
    )
    input_snapshot = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(completed_at__isnull=True) | Q(completed_at__gte=F("started_at")),
                name="calculation_completed_after_started",
            ),
        ]

    def clean(self):
        if self.scenario_version_id and self.scenario_version.scenario.organization_id != self.organization_id:
            raise ValidationError("Calculation scenario must belong to the run organization.")

class PlanningFact(TimeStampedModel):
    calculation_run = models.ForeignKey(
        CalculationRun, on_delete=models.CASCADE, related_name="facts"
    )
    scenario_version = models.ForeignKey(
        ScenarioVersion, on_delete=models.PROTECT, related_name="planning_facts"
    )
    fiscal_period = models.ForeignKey(
        FiscalPeriod, on_delete=models.PROTECT, related_name="planning_facts"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="planning_facts"
    )
    group_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="planning_facts"
    )
    entity_account = models.ForeignKey(
        EntityAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_facts",
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="planning_facts"
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_facts",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_facts",
    )
    profit_center = models.ForeignKey(
        ProfitCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_facts",
    )
    business_unit = models.ForeignKey(
        BusinessUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_facts",
    )
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.PROTECT, related_name="planning_facts"
    )
    source_kind = models.CharField(max_length=16, choices=PlanningFactSource.choices)
    source_rule = models.ForeignKey(
        CalculationRule,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_facts",
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="planning_facts"
    )
    lineage = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["fiscal_period_id", "legal_entity_id", "group_account_id"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "calculation_run",
                    "scenario_version",
                    "fiscal_period",
                    "legal_entity",
                    "group_account",
                    "entity_account",
                    "branch",
                    "department",
                    "cost_center",
                    "profit_center",
                    "business_unit",
                    "project",
                ],
                nulls_distinct=False,
                name="uniq_planning_fact_grain",
            ),
        ]

    def clean(self):
        if self.calculation_run_id and self.calculation_run.scenario_version_id != self.scenario_version_id:
            raise ValidationError("Planning fact and calculation run must use the same scenario version.")
        if self.legal_entity_id and self.legal_entity.organization_id != self.scenario_version.scenario.organization_id:
            raise ValidationError("Planning fact entity must belong to the scenario organization.")
        if self.group_account_id and self.group_account.organization_id != self.scenario_version.scenario.organization_id:
            raise ValidationError("Planning fact account must belong to the scenario organization.")
        if self.source_rule_id and self.source_rule.organization_id != self.scenario_version.scenario.organization_id:
            raise ValidationError("Planning fact rule must belong to the scenario organization.")
        if self.source_rule_id and self.source_rule.scenario_version_id not in (
            None,
            self.scenario_version_id,
        ):
            raise ValidationError("Planning fact rule must be global or use the same scenario version.")
        if self.entity_account_id and self.entity_account.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Planning fact local account must belong to the fact entity.")
        if self.branch_id and self.branch.legal_entity_id not in (None, self.legal_entity_id):
            raise ValidationError("Planning fact branch must belong to the fact entity.")
        if self.department_id and self.department.legal_entity_id not in (
            None,
            self.legal_entity_id,
        ):
            raise ValidationError("Planning fact department must belong to the fact entity.")
        if self.cost_center_id and self.cost_center.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Planning fact cost center must belong to the fact entity.")
        if self.profit_center_id and self.profit_center.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Planning fact profit center must belong to the fact entity.")
        if self.business_unit_id and self.business_unit.organization_id != self.scenario_version.scenario.organization_id:
            raise ValidationError("Planning fact business unit must belong to the scenario organization.")
        if self.project_id and self.project.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Planning fact project must belong to the fact entity.")

__all__ = ['PlanningAssumption', 'PlanningDriver', 'DriverValue', 'CalculationRule', 'CalculationRuleDependency', 'AllocationRule', 'AllocationRuleLine', 'CalculationRun', 'PlanningFact']
