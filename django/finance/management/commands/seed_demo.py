from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from finance.models import Branch, Department, Expense


class Command(BaseCommand):
    help = "Create repeatable educational finance data."

    def handle(self, *args, **options):
        branches = {
            "AMM": ("Amman Branch", "Amman"),
            "IRB": ("Irbid Branch", "Irbid"),
            "AQB": ("Aqaba Branch", "Aqaba"),
        }
        department_names = {
            "SALES": "Sales",
            "OPS": "Operations",
            "HR": "Human Resources",
            "FIN": "Finance",
        }

        department_by_code = {}
        for branch_code, (branch_name, city) in branches.items():
            branch, _ = Branch.objects.update_or_create(
                code=branch_code,
                defaults={"name": branch_name, "city": city, "is_active": True},
            )
            for department_code, department_name in department_names.items():
                code = f"{branch_code}-{department_code}"
                department, _ = Department.objects.update_or_create(
                    code=code,
                    defaults={"name": department_name, "branch": branch},
                )
                department_by_code[code] = department

        expenses = [
            ("AMM-OPS", date(2026, 1, 5), "Branch rent", "2500.00"),
            ("AMM-HR", date(2026, 1, 10), "Staff training", "450.00"),
            ("IRB-OPS", date(2026, 1, 7), "Utilities", "780.00"),
            ("IRB-SALES", date(2026, 1, 15), "Sales campaign", "1200.00"),
            ("AQB-OPS", date(2026, 1, 8), "Warehouse rent", "1800.00"),
            ("AQB-FIN", date(2026, 1, 20), "Bank fees", "95.00"),
        ]

        for department_code, expense_date, description, amount in expenses:
            Expense.objects.update_or_create(
                department=department_by_code[department_code],
                expense_date=expense_date,
                description=description,
                defaults={"amount": Decimal(amount), "currency": "USD"},
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Branch.objects.count()} branches, "
                f"{Department.objects.count()} departments, and "
                f"{Expense.objects.count()} expenses."
            )
        )