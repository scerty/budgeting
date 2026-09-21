from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from finance.models import (
    Branch,
    BusinessUnit,
    ConsolidationMethod,
    CostCenter,
    Currency,
    Department,
    EntityBusinessUnitAssignment,
    FiscalCalendar,
    LegalEntity,
    Organization,
    OwnershipPeriod,
)


START_DATE = date(2026, 1, 1)
BRANCHES = {
    "AMM": "Amman",
    "IRB": "Irbid",
    "AQB": "Aqaba",
}
DEPARTMENTS = {
    "FIN": "Finance",
    "HR": "Human Resources",
    "OPS": "Operations",
    "SALES": "Sales",
    "IT": "Information Technology",
}
ENTITIES = {
    "ERP-FD": "Finance Demo",
    "ERP-FDD": "Finance Demo (Demo)",
}


class Command(BaseCommand):
    help = "Build an idempotent demo holding, subsidiaries, branches, departments, and cost centers."

    def add_arguments(self, parser):
        parser.add_argument("--organization", default="DEMO")

    def handle(self, *args, **options):
        try:
            organization = Organization.objects.get(code=options["organization"])
            currency = Currency.objects.get(code="USD")
            calendar = FiscalCalendar.objects.get(
                organization=organization, code="CAL-2026"
            )
        except (Organization.DoesNotExist, Currency.DoesNotExist, FiscalCalendar.DoesNotExist) as exc:
            raise CommandError("DEMO organization, USD currency, or CAL-2026 is missing.") from exc

        with transaction.atomic():
            holding = self.ensure_entity(
                organization,
                currency,
                calendar,
                "ERP-GROUP",
                "Finance Demo Group Holding",
                None,
            )
            entities = {
                code: self.ensure_entity(
                    organization,
                    currency,
                    calendar,
                    code,
                    name,
                    holding,
                )
                for code, name in ENTITIES.items()
            }
            self.ensure_ownership(organization, holding, entities.values())
            branches = self.ensure_branches(entities)
            departments = self.ensure_departments(entities, branches)
            business_units = self.ensure_business_units(organization)
            self.ensure_business_unit_assignments(entities.values(), business_units)
            cost_centers = self.ensure_cost_centers(entities, branches, departments)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo group structure built: "
                f"holding=1 subsidiaries={len(entities)} "
                f"branches={len(branches)} departments={len(departments)} "
                f"business_units={len(business_units)} cost_centers={len(cost_centers)}"
            )
        )

    @staticmethod
    def ensure_entity(organization, currency, calendar, code, name, parent):
        entity, _ = LegalEntity.objects.update_or_create(
            organization=organization,
            code=code,
            defaults={
                "legal_name": name,
                "short_name": code,
                "functional_currency": currency,
                "reporting_currency": currency,
                "fiscal_calendar": calendar,
                "parent_entity": parent,
                "consolidation_method": ConsolidationMethod.FULL,
                "valid_from": START_DATE,
            },
        )
        return entity

    @staticmethod
    def ensure_ownership(organization, holding, entities):
        for entity in entities:
            OwnershipPeriod.objects.update_or_create(
                organization=organization,
                parent_entity=holding,
                child_entity=entity,
                valid_from=START_DATE,
                defaults={
                    "ownership_percentage": 100,
                    "control_percentage": 100,
                    "consolidation_method": ConsolidationMethod.FULL,
                },
            )

    @staticmethod
    def ensure_branches(entities):
        branches = {}
        for entity_code, entity in entities.items():
            for branch_code, city in BRANCHES.items():
                branch, _ = Branch.objects.update_or_create(
                    legal_entity=entity,
                    code=branch_code,
                    defaults={
                        "name": f"{city} Branch",
                        "city": city,
                        "timezone": "Asia/Amman",
                    },
                )
                branches[(entity_code, branch_code)] = branch
        return branches

    @staticmethod
    def ensure_departments(entities, branches):
        departments = {}
        for entity_code, entity in entities.items():
            for branch_code in BRANCHES:
                branch = branches[(entity_code, branch_code)]
                for department_code, name in DEPARTMENTS.items():
                    entity_prefix = entity_code.removeprefix("ERP-")
                    code = f"{entity_prefix}-{branch_code}-{department_code}"
                    department, _ = Department.objects.update_or_create(
                        branch=branch,
                        code=code,
                        defaults={
                            "name": name,
                            "legal_entity": entity,
                            "is_active": True,
                        },
                    )
                    departments[(entity_code, branch_code, department_code)] = department
        return departments

    @staticmethod
    def ensure_business_units(organization):
        root, _ = BusinessUnit.objects.update_or_create(
            organization=organization,
            code="BU-GROUP",
            defaults={"name": "Group Shared Structure", "parent": None},
        )
        business_units = {"BU-GROUP": root}
        for code, name in {
            "BU-SHARED": "Shared Services",
            "BU-COMMERCIAL": "Commercial",
            "BU-OPERATIONS": "Operations",
        }.items():
            unit, _ = BusinessUnit.objects.update_or_create(
                organization=organization,
                code=code,
                defaults={"name": name, "parent": root},
            )
            business_units[code] = unit
        return business_units

    @staticmethod
    def ensure_business_unit_assignments(entities, business_units):
        for entity in entities:
            for code in ("BU-SHARED", "BU-COMMERCIAL", "BU-OPERATIONS"):
                EntityBusinessUnitAssignment.objects.get_or_create(
                    legal_entity=entity,
                    business_unit=business_units[code],
                    valid_from=START_DATE,
                )

    @staticmethod
    def ensure_cost_centers(entities, branches, departments):
        cost_centers = {}
        for entity_code, entity in entities.items():
            for branch_code in BRANCHES:
                branch = branches[(entity_code, branch_code)]
                branch_center, _ = CostCenter.objects.update_or_create(
                    legal_entity=entity,
                    code=branch_code,
                    defaults={
                        "name": f"{branch.city} Branch",
                        "branch": branch,
                        "department": None,
                        "parent": None,
                    },
                )
                cost_centers[(entity_code, branch_code)] = branch_center
                for department_code in DEPARTMENTS:
                    department = departments[(entity_code, branch_code, department_code)]
                    code = f"{branch_code}-{department_code}"
                    center, _ = CostCenter.objects.update_or_create(
                        legal_entity=entity,
                        code=code,
                        defaults={
                            "name": f"{branch.city} / {department.name}",
                            "parent": branch_center,
                            "branch": branch,
                            "department": department,
                        },
                    )
                    cost_centers[(entity_code, code)] = center
        return cost_centers