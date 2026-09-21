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


class Scenario(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="planning_scenarios"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    scenario_type = models.CharField(max_length=24, choices=ScenarioType.choices)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_planning_scenarios",
    )
    status = models.CharField(
        max_length=16, choices=ScenarioStatus.choices, default=ScenarioStatus.DRAFT
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_scenario_code_org"
            ),
        ]

class ScenarioVersion(TimeStampedModel):
    scenario = models.ForeignKey(
        Scenario, on_delete=models.CASCADE, related_name="versions"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    version_number = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=16,
        choices=ScenarioVersionStatus.choices,
        default=ScenarioVersionStatus.DRAFT,
    )
    based_on = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="derived_versions",
    )
    is_final = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="locked_scenario_versions",
    )

    class Meta:
        ordering = ["scenario_id", "version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["scenario", "code"], name="uniq_scenario_version_code"
            ),
            models.UniqueConstraint(
                fields=["scenario", "version_number"],
                name="uniq_scenario_version_number",
            ),
            models.CheckConstraint(
                condition=Q(version_number__gte=1),
                name="scenario_version_number_positive",
            ),
        ]

    def clean(self):
        if self.based_on_id and self.based_on_id == self.pk:
            raise ValidationError("A scenario version cannot be based on itself.")
        if self.based_on_id and self.based_on.scenario_id != self.scenario_id:
            raise ValidationError("Scenario versions must be based on the same scenario.")

class ScenarioBlend(TimeStampedModel):
    result_version = models.ForeignKey(
        ScenarioVersion, on_delete=models.CASCADE, related_name="blend_components"
    )
    source_kind = models.CharField(max_length=16, choices=ScenarioBlendSource.choices)
    source_version = models.ForeignKey(
        ScenarioVersion,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="blend_usages",
    )
    fiscal_period_from = models.ForeignKey(
        FiscalPeriod,
        on_delete=models.PROTECT,
        related_name="scenario_blends_from",
    )
    fiscal_period_to = models.ForeignKey(
        FiscalPeriod,
        on_delete=models.PROTECT,
        related_name="scenario_blends_to",
    )
    priority = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["result_version_id", "priority", "fiscal_period_from_id"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "result_version",
                    "source_kind",
                    "source_version",
                    "fiscal_period_from",
                    "fiscal_period_to",
                    "priority",
                ],
                nulls_distinct=False,
                name="uniq_scenario_blend_component",
            ),
        ]

    def clean(self):
        if self.source_kind == ScenarioBlendSource.PLANNING and not self.source_version_id:
            raise ValidationError("Planning blend components require a source version.")
        if self.source_kind == ScenarioBlendSource.ACTUALS and self.source_version_id:
            raise ValidationError("Actuals blend components cannot have a source version.")
        if self.source_version_id and (
            self.source_version.scenario.organization_id
            != self.result_version.scenario.organization_id
        ):
            raise ValidationError("Blend source and result must share an organization.")
        if self.fiscal_period_from.calendar_id != self.fiscal_period_to.calendar_id:
            raise ValidationError("Blend periods must use the same fiscal calendar.")
        if self.fiscal_period_from.start_date > self.fiscal_period_to.start_date:
            raise ValidationError("Blend period start must not follow its end.")
        result_calendar_id = getattr(
            self.result_version.scenario.organization.default_fiscal_calendar,
            "id",
            None,
        )
        if result_calendar_id and result_calendar_id != self.fiscal_period_from.calendar_id:
            raise ValidationError("Blend periods must use the scenario organization calendar.")

        if self.result_version_id and self.priority is not None:
            start_date = self.fiscal_period_from.start_date
            end_date = self.fiscal_period_to.end_date
            existing_components = ScenarioBlend.objects.filter(
                result_version_id=self.result_version_id,
                priority=self.priority,
            ).exclude(pk=self.pk)
            for component in existing_components.select_related(
                "fiscal_period_from", "fiscal_period_to"
            ):
                if (
                    component.fiscal_period_from.start_date <= end_date
                    and component.fiscal_period_to.end_date >= start_date
                ):
                    raise ValidationError(
                        "Blend components at the same priority cannot overlap."
                    )

class BudgetPlan(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="budget_plans"
    )
    fiscal_calendar = models.ForeignKey(
        FiscalCalendar, null=True, blank=True, on_delete=models.PROTECT, related_name="budget_plans"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_budget_plans",
    )
    status = models.CharField(
        max_length=16, choices=BudgetStatus.choices, default=BudgetStatus.DRAFT
    )

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_budget_plan_code_org"
            ),
        ]

    def clean(self):
        if self.fiscal_calendar_id and self.fiscal_calendar.organization_id != self.organization_id:
            raise ValidationError("Budget calendar must belong to the same organization.")

class BudgetVersion(TimeStampedModel):
    plan = models.ForeignKey(BudgetPlan, on_delete=models.CASCADE, related_name="versions")
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    version_type = models.CharField(max_length=16, choices=BudgetVersionType.choices)
    scenario = models.CharField(max_length=50, default="BASE")
    scenario_version = models.ForeignKey(
        ScenarioVersion,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="budget_versions",
    )
    status = models.CharField(
        max_length=16, choices=BudgetStatus.choices, default=BudgetStatus.DRAFT
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_budget_versions",
    )

    class Meta:
        ordering = ["plan_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "code"], name="uniq_budget_version_code_plan"
            ),
        ]

    def clean(self):
        if self.status == BudgetStatus.APPROVED and not self.approved_at:
            raise ValidationError("Approved budget versions require approved_at.")
        if self.scenario_version_id:
            if self.scenario_version.scenario.organization_id != self.plan.organization_id:
                raise ValidationError("Scenario version and budget plan must share an organization.")

class BudgetLine(TimeStampedModel):
    version = models.ForeignKey(
        BudgetVersion, on_delete=models.CASCADE, related_name="lines"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="budget_lines"
    )
    fiscal_period = models.ForeignKey(
        FiscalPeriod, on_delete=models.PROTECT, related_name="budget_lines"
    )
    group_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="budget_lines"
    )
    entity_account = models.ForeignKey(
        EntityAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="budget_lines",
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="budget_lines"
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="budget_lines",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="budget_lines",
    )
    profit_center = models.ForeignKey(
        ProfitCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="budget_lines",
    )
    business_unit = models.ForeignKey(
        BusinessUnit,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="budget_lines",
    )
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.PROTECT, related_name="budget_lines"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="budget_lines"
    )
    budget_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_budget_lines",
    )

    class Meta:
        ordering = ["fiscal_period_id", "legal_entity_id", "group_account_id"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "version",
                    "legal_entity",
                    "fiscal_period",
                    "group_account",
                    "entity_account",
                    "branch",
                    "department",
                    "cost_center",
                    "profit_center",
                    "business_unit",
                    "project",
                ],
                name="uniq_budget_line_grain",
                nulls_distinct=False,
            ),
        ]

    def clean(self):
        if self.version_id and self.legal_entity_id:
            if self.version.plan.organization_id != self.legal_entity.organization_id:
                raise ValidationError("Budget version and entity must share an organization.")
        if self.fiscal_period_id and self.legal_entity_id:
            if self.fiscal_period.calendar_id != self.legal_entity.fiscal_calendar_id:
                raise ValidationError("Budget period must use the entity fiscal calendar.")
        if self.group_account_id and self.legal_entity_id:
            if self.group_account.organization_id != self.legal_entity.organization_id:
                raise ValidationError("Group account and entity must share an organization.")
        if self.entity_account_id and self.entity_account.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Local account must belong to the budget entity.")
        if self.branch_id and self.branch.legal_entity_id not in (None, self.legal_entity_id):
            raise ValidationError("Budget branch must belong to the budget entity.")
        if self.department_id and self.department.legal_entity_id not in (
            None,
            self.legal_entity_id,
        ):
            raise ValidationError("Budget department must belong to the budget entity.")
        if self.cost_center_id and self.cost_center.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Budget cost center must belong to the budget entity.")
        if self.profit_center_id and self.profit_center.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Budget profit center must belong to the budget entity.")
        if self.business_unit_id and self.business_unit.organization_id != self.legal_entity.organization_id:
            raise ValidationError("Budget business unit must belong to the budget organization.")
        if self.project_id and self.project.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Budget project must belong to the budget entity.")

__all__ = ['Scenario', 'ScenarioVersion', 'ScenarioBlend', 'BudgetPlan', 'BudgetVersion', 'BudgetLine']
