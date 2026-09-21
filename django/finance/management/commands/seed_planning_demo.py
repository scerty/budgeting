from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from finance.models import (
    BudgetLine,
    BudgetPlan,
    BudgetStatus,
    BudgetVersion,
    BudgetVersionType,
    CalculationRun,
    CalculationRunStatus,
    Currency,
    DriverValue,
    FiscalPeriod,
    GroupAccount,
    LegalEntity,
    Organization,
    PlanningDriver,
    PlanningFact,
    PlanningFactSource,
    Scenario,
    ScenarioStatus,
    ScenarioType,
    ScenarioVersion,
    ScenarioVersionStatus,
)


class Command(BaseCommand):
    help = "Create repeatable budget and planning data for analytics validation."

    @transaction.atomic
    def handle(self, *args, **options):
        organization = Organization.objects.order_by("id").first()
        if not organization:
            raise CommandError("Seed master data first: no Organization exists.")

        currency = Currency.objects.filter(code="USD").first()
        if not currency:
            currency = organization.default_reporting_currency
        if not currency:
            raise CommandError("Seed a reporting currency before planning demo data.")

        calendar = organization.default_fiscal_calendar
        if not calendar:
            raise CommandError("Seed a fiscal calendar before planning demo data.")

        period = FiscalPeriod.objects.filter(calendar=calendar).order_by("start_date").first()
        legal_entity = LegalEntity.objects.filter(organization=organization).order_by("id").first()
        group_account = (
            GroupAccount.objects.filter(organization=organization, is_posting_allowed=True)
            .order_by("id")
            .first()
        )
        if not period or not legal_entity or not group_account:
            raise CommandError(
                "Seed a fiscal period, legal entity, and posting group account first."
            )

        branch = legal_entity.branches.order_by("id").first()
        department = branch.departments.order_by("id").first() if branch else None

        scenario, _ = Scenario.objects.update_or_create(
            organization=organization,
            code="DEMO-BASE",
            defaults={
                "name": "Demo base plan",
                "scenario_type": ScenarioType.BUDGET,
                "status": ScenarioStatus.ACTIVE,
                "is_active": True,
            },
        )
        scenario_version, _ = ScenarioVersion.objects.update_or_create(
            scenario=scenario,
            code="DEMO-BASE-V1",
            defaults={
                "name": "Demo base plan version 1",
                "version_number": 1,
                "status": ScenarioVersionStatus.APPROVED,
                "is_final": True,
            },
        )

        plan, _ = BudgetPlan.objects.update_or_create(
            organization=organization,
            code="DEMO-2026",
            defaults={
                "fiscal_calendar": calendar,
                "name": "Demo 2026 budget",
                "status": BudgetStatus.APPROVED,
            },
        )
        budget_version, _ = BudgetVersion.objects.update_or_create(
            plan=plan,
            code="DEMO-2026-ORIGINAL",
            defaults={
                "name": "Demo 2026 original budget",
                "version_type": BudgetVersionType.ORIGINAL,
                "scenario": "BASE",
                "scenario_version": scenario_version,
                "status": BudgetStatus.APPROVED,
                "approved_at": timezone.now(),
            },
        )
        BudgetLine.objects.update_or_create(
            version=budget_version,
            legal_entity=legal_entity,
            fiscal_period=period,
            group_account=group_account,
            entity_account=None,
            branch=branch,
            department=department,
            cost_center=None,
            profit_center=None,
            business_unit=None,
            project=None,
            defaults={
                "amount": Decimal("7000.00"),
                "currency": currency,
            },
        )

        driver, _ = PlanningDriver.objects.update_or_create(
            organization=organization,
            code="DEMO-HEADCOUNT",
            defaults={
                "name": "Demo headcount",
                "unit": "FTE",
                "is_active": True,
            },
        )
        DriverValue.objects.update_or_create(
            driver=driver,
            scenario_version=scenario_version,
            fiscal_period=period,
            legal_entity=legal_entity,
            branch=branch,
            department=department,
            project=None,
            defaults={
                "value": Decimal("120.000000"),
                "currency": currency,
                "source": "seed_planning_demo",
            },
        )

        run = CalculationRun.objects.filter(
            scenario_version=scenario_version,
            input_snapshot__contains={"seed_key": "finance-planning-demo"},
        ).first()
        if not run:
            run = CalculationRun(
                organization=organization,
                scenario_version=scenario_version,
                input_snapshot={"seed_key": "finance-planning-demo"},
            )
        run.organization = organization
        run.status = CalculationRunStatus.SUCCEEDED
        run.started_at = timezone.now()
        run.completed_at = timezone.now()
        run.error_message = ""
        run.save()

        PlanningFact.objects.update_or_create(
            calculation_run=run,
            scenario_version=scenario_version,
            fiscal_period=period,
            legal_entity=legal_entity,
            group_account=group_account,
            entity_account=None,
            branch=branch,
            department=department,
            cost_center=None,
            profit_center=None,
            business_unit=None,
            project=None,
            defaults={
                "source_kind": PlanningFactSource.CALCULATED,
                "amount": Decimal("7200.00"),
                "currency": currency,
                "lineage": {"seed_key": "finance-planning-demo"},
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded one approved budget line, one planning driver value, "
                "and one succeeded planning fact."
            )
        )