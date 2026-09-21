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
from .reporting import *  # noqa: F401,F403


class ConsolidationGroup(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="consolidation_groups"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    parent_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="consolidation_groups"
    )
    reporting_currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="consolidation_groups"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_consolidation_group_code_org"
            ),
        ]

    def clean(self):
        if self.parent_entity_id and self.parent_entity.organization_id != self.organization_id:
            raise ValidationError("Consolidation parent entity must belong to the organization.")

    def __str__(self):
        return f"{self.organization.code} / {self.code}"

class ConsolidationScope(TimeStampedModel):
    group = models.ForeignKey(
        ConsolidationGroup, on_delete=models.CASCADE, related_name="scopes"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="consolidation_scopes"
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["group_id", "valid_from", "legal_entity_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "legal_entity", "valid_from"],
                name="uniq_consolidation_scope_start",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="consolidation_scope_valid_dates",
            ),
        ]

    def clean(self):
        if self.legal_entity_id and self.legal_entity.organization_id != self.group.organization_id:
            raise ValidationError("Consolidation scope entity must belong to the group organization.")

class IntercompanyPair(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="intercompany_pairs"
    )
    entity_a = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="intercompany_pairs_as_a"
    )
    entity_b = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="intercompany_pairs_as_b"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "entity_a_id", "entity_b_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "entity_a", "entity_b"],
                name="uniq_intercompany_pair",
            ),
            models.CheckConstraint(
                condition=~Q(entity_a=F("entity_b")),
                name="intercompany_pair_distinct_entities",
            ),
        ]

    def clean(self):
        if self.entity_a_id and self.entity_a.organization_id != self.organization_id:
            raise ValidationError("Intercompany entity A must belong to the organization.")
        if self.entity_b_id and self.entity_b.organization_id != self.organization_id:
            raise ValidationError("Intercompany entity B must belong to the organization.")
        if self.entity_a_id and self.entity_b_id and self.entity_a_id > self.entity_b_id:
            raise ValidationError("Store intercompany pairs in ascending entity order.")

    def __str__(self):
        return f"{self.entity_a.code} <-> {self.entity_b.code}"

class EliminationRule(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="elimination_rules"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    account_at_entity_a = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="elimination_rules_as_a"
    )
    account_at_entity_b = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="elimination_rules_as_b"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_elimination_rule_code_org"
            ),
        ]

    def clean(self):
        if self.account_at_entity_a_id and self.account_at_entity_a.organization_id != self.organization_id:
            raise ValidationError("Elimination account A must belong to the organization.")
        if self.account_at_entity_b_id and self.account_at_entity_b.organization_id != self.organization_id:
            raise ValidationError("Elimination account B must belong to the organization.")

    def __str__(self):
        return self.name

class ConsolidationRun(TimeStampedModel):
    group = models.ForeignKey(
        ConsolidationGroup, on_delete=models.PROTECT, related_name="runs"
    )
    fiscal_period = models.ForeignKey(
        FiscalPeriod, on_delete=models.PROTECT, related_name="consolidation_runs"
    )
    data_set = models.CharField(max_length=10, choices=ConsolidationDataSet.choices)
    scenario_version = models.ForeignKey(
        BudgetVersion,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="consolidation_runs",
    )
    status = models.CharField(
        max_length=16,
        choices=ConsolidationRunStatus.choices,
        default=ConsolidationRunStatus.RUNNING,
    )
    started_at = models.DateTimeField(default=timezone.now)
    executed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="consolidation_runs",
    )
    is_final = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(completed_at__isnull=True) | Q(completed_at__gte=F("started_at")),
                name="consolidation_completed_after_started",
            ),
        ]

    def clean(self):
        if self.group_id and self.fiscal_period_id:
            if self.fiscal_period.calendar_id != self.group.parent_entity.fiscal_calendar_id:
                raise ValidationError("Consolidation period must use the parent entity calendar.")
        if self.data_set == ConsolidationDataSet.PLANNING and not self.scenario_version_id:
            raise ValidationError("Planning consolidation runs require a scenario version.")
        if self.data_set == ConsolidationDataSet.ACTUALS and self.scenario_version_id:
            raise ValidationError("Actual consolidation runs cannot have a scenario version.")
        if self.scenario_version_id:
            if self.scenario_version.plan.organization_id != self.group.organization_id:
                raise ValidationError("Scenario version must belong to the group organization.")
            if (
                self.scenario_version.plan.fiscal_calendar_id
                and self.scenario_version.plan.fiscal_calendar_id
                != self.group.parent_entity.fiscal_calendar_id
            ):
                raise ValidationError("Scenario version must use the parent entity calendar.")

    def __str__(self):
        return f"{self.group.code} - {self.fiscal_period} ({self.data_set})"

class EliminationEntry(TimeStampedModel):
    run = models.ForeignKey(
        ConsolidationRun, on_delete=models.CASCADE, related_name="elimination_entries"
    )
    rule = models.ForeignKey(
        EliminationRule,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="entries",
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="elimination_entries"
    )
    group_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="elimination_entries"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)

    def clean(self):
        if self.legal_entity_id and self.legal_entity.organization_id != self.run.group.organization_id:
            raise ValidationError("Elimination entity must belong to the run organization.")
        if self.group_account_id and self.group_account.organization_id != self.run.group.organization_id:
            raise ValidationError("Elimination account must belong to the run organization.")

    def __str__(self):
        return f"{self.legal_entity.code} / {self.group_account.code}: {self.amount}"

class MinorityInterestEntry(TimeStampedModel):
    run = models.ForeignKey(
        ConsolidationRun, on_delete=models.CASCADE, related_name="minority_entries"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="minority_entries"
    )
    group_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="minority_entries"
    )
    pre_minority_amount = models.DecimalField(max_digits=18, decimal_places=2)
    minority_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    minority_amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(minority_percentage__gte=0) & Q(minority_percentage__lte=100)),
                name="minority_percentage_range",
            ),
        ]

    def clean(self):
        if self.legal_entity_id and self.legal_entity.organization_id != self.run.group.organization_id:
            raise ValidationError("Minority entity must belong to the run organization.")
        if self.group_account_id and self.group_account.organization_id != self.run.group.organization_id:
            raise ValidationError("Minority account must belong to the run organization.")

    def __str__(self):
        return f"{self.legal_entity.code} / {self.group_account.code}: {self.minority_amount}"

class TranslationAdjustment(TimeStampedModel):
    run = models.ForeignKey(
        ConsolidationRun, on_delete=models.CASCADE, related_name="translation_entries"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="translation_entries"
    )
    group_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="translation_entries"
    )
    local_amount = models.DecimalField(max_digits=18, decimal_places=2)
    rate_used = models.DecimalField(max_digits=18, decimal_places=8)
    translated_amount = models.DecimalField(max_digits=18, decimal_places=2)
    cta_amount = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(rate_used__gt=0), name="translation_rate_positive"),
        ]

    def clean(self):
        if self.legal_entity_id and self.legal_entity.organization_id != self.run.group.organization_id:
            raise ValidationError("Translation entity must belong to the run organization.")
        if self.group_account_id and self.group_account.organization_id != self.run.group.organization_id:
            raise ValidationError("Translation account must belong to the run organization.")

    def __str__(self):
        return f"{self.legal_entity.code} / {self.group_account.code}: {self.translated_amount}"

class GoodwillCalculation(TimeStampedModel):
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="goodwill_calculations"
    )
    purchase_price = models.DecimalField(max_digits=18, decimal_places=2)
    net_assets_at_acquisition = models.DecimalField(max_digits=18, decimal_places=2)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    goodwill_amount = models.DecimalField(max_digits=18, decimal_places=2)
    amortisation_years = models.PositiveIntegerField(default=10)
    goodwill_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="goodwill_calculations"
    )
    amortisation_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="goodwill_amortisation_calculations"
    )
    acquisition_date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(ownership_percentage__gte=0) & Q(ownership_percentage__lte=100)),
                name="goodwill_ownership_percentage_range",
            ),
            models.CheckConstraint(
                condition=Q(amortisation_years__gte=1), name="goodwill_amortisation_years_positive"
            ),
        ]

    def clean(self):
        if self.goodwill_account_id and self.goodwill_account.organization_id != self.legal_entity.organization_id:
            raise ValidationError("Goodwill account must belong to the entity organization.")
        if self.amortisation_account_id and self.amortisation_account.organization_id != self.legal_entity.organization_id:
            raise ValidationError("Amortisation account must belong to the entity organization.")

    def __str__(self):
        return f"Goodwill: {self.legal_entity.code} = {self.goodwill_amount}"

class IntercompanyInventoryElimination(TimeStampedModel):
    run = models.ForeignKey(
        ConsolidationRun, on_delete=models.CASCADE, related_name="inventory_eliminations"
    )
    selling_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="inventory_sales_eliminations"
    )
    buying_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="inventory_purchase_eliminations"
    )
    inventory_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="inventory_eliminations"
    )
    cogs_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="inventory_cogs_eliminations"
    )
    intercompany_inventory_balance = models.DecimalField(max_digits=18, decimal_places=2)
    profit_margin_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    unrealised_profit = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(profit_margin_percentage__gte=0) & Q(profit_margin_percentage__lte=100)),
                name="inventory_profit_margin_range",
            ),
            models.CheckConstraint(
                condition=~Q(selling_entity=F("buying_entity")),
                name="inventory_elimination_distinct_entities",
            ),
        ]

    def clean(self):
        if self.selling_entity_id and self.selling_entity.organization_id != self.run.group.organization_id:
            raise ValidationError("Selling entity must belong to the run organization.")
        if self.buying_entity_id and self.buying_entity.organization_id != self.run.group.organization_id:
            raise ValidationError("Buying entity must belong to the run organization.")
        if self.inventory_account_id and self.inventory_account.organization_id != self.run.group.organization_id:
            raise ValidationError("Inventory account must belong to the run organization.")
        if self.cogs_account_id and self.cogs_account.organization_id != self.run.group.organization_id:
            raise ValidationError("COGS account must belong to the run organization.")

    def __str__(self):
        return (
            f"IC inventory profit elimination: {self.selling_entity.code} -> "
            f"{self.buying_entity.code}: {self.unrealised_profit}"
        )

class IntercompanyMatch(TimeStampedModel):
    run = models.ForeignKey(
        ConsolidationRun, on_delete=models.CASCADE, related_name="intercompany_matches"
    )
    pair = models.ForeignKey(
        IntercompanyPair, on_delete=models.PROTECT, related_name="matches"
    )
    rule = models.ForeignKey(
        EliminationRule, on_delete=models.PROTECT, related_name="matches"
    )
    amount_entity_a = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    amount_entity_b = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    difference = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    status = models.CharField(
        max_length=10,
        choices=IntercompanyMatchStatus.choices,
        default=IntercompanyMatchStatus.UNKNOWN,
    )
    no_part = models.BooleanField(default=False)
    manual_correction = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    matched_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["run", "pair", "rule"], name="uniq_intercompany_match"
            ),
        ]

    def clean(self):
        if self.pair_id and self.pair.organization_id != self.run.group.organization_id:
            raise ValidationError("Intercompany pair must belong to the run organization.")
        if self.rule_id and self.rule.organization_id != self.run.group.organization_id:
            raise ValidationError("Elimination rule must belong to the run organization.")

    def __str__(self):
        return f"{self.pair} / {self.rule.code}: {self.status}"

__all__ = ['ConsolidationGroup', 'ConsolidationScope', 'IntercompanyPair', 'EliminationRule', 'ConsolidationRun', 'EliminationEntry', 'MinorityInterestEntry', 'TranslationAdjustment', 'GoodwillCalculation', 'IntercompanyInventoryElimination', 'IntercompanyMatch']
