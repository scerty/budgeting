import hashlib
import re
import os
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from finance.ingestion.erpnext import ERPNextAPIError, ERPNextClient
from finance.models import (
    AccountType,
    Branch,
    CostCenter,
    Currency,
    EntityAccount,
    FiscalCalendar,
    GroupAccount,
    LegalEntity,
    NormalBalance,
    Organization,
)


COMPANY_FIELDS = ["name", "abbr", "default_currency", "country"]
ACCOUNT_FIELDS = [
    "name",
    "account_name",
    "parent_account",
    "root_type",
    "account_type",
    "is_group",
    "disabled",
    "company",
    "lft",
]
COST_CENTER_FIELDS = [
    "name",
    "cost_center_name",
    "parent_cost_center",
    "company",
    "is_group",
    "disabled",
    "lft",
]


def compact_code(value, prefix="ERP", limit=30):
    normalized = re.sub(r"[^A-Z0-9]+", "-", str(value).upper()).strip("-")
    if len(normalized) <= limit:
        return normalized
    digest = hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:8].upper()
    return f"{normalized[:limit - len(prefix) - 10]}-{digest}"[:limit]


def account_type_for(row):
    return {
        "Asset": AccountType.ASSET,
        "Liability": AccountType.LIABILITY,
        "Equity": AccountType.EQUITY,
        "Income": AccountType.REVENUE,
        "Expense": AccountType.OPERATING_EXPENSE,
    }.get(row.get("root_type"), AccountType.STATISTICAL)


def normal_balance_for(row):
    return (
        NormalBalance.DEBIT
        if row.get("root_type") in {"Asset", "Expense"}
        else NormalBalance.CREDIT
    )


class Command(BaseCommand):
    help = "Synchronize ERPNext companies, accounts, cost centers, and branches into Django."

    def add_arguments(self, parser):
        parser.add_argument("--organization", default="DEMO")
        parser.add_argument(
            "--base-url",
            default=os.environ.get("ERPNEXT_URL", "http://host.docker.internal:18080"),
        )
        parser.add_argument("--username", default=os.environ.get("ERPNEXT_USER", "Administrator"))
        parser.add_argument("--password", default=os.environ.get("ERPNEXT_PASSWORD"))
        parser.add_argument("--branch-company", default="Finance Demo (Demo)")
        parser.add_argument("--fiscal-calendar", default="CAL-2026")

    def handle(self, *args, **options):
        if not options["password"]:
            raise CommandError("Pass --password or set ERPNEXT_PASSWORD.")
        try:
            organization = Organization.objects.get(code=options["organization"])
        except Organization.DoesNotExist as exc:
            raise CommandError(f"Unknown Django organization: {options['organization']}") from exc

        client = ERPNextClient(
            base_url=options["base_url"],
            username=options["username"],
            password=options["password"],
        )
        try:
            client.login()
            companies = list(client.iter_resource("Company", COMPANY_FIELDS, page_size=100))
            accounts = list(client.iter_resource("Account", ACCOUNT_FIELDS, page_size=200))
            cost_centers = list(
                client.iter_resource("Cost Center", COST_CENTER_FIELDS, page_size=100)
            )
            branches = list(client.iter_resource("Branch", ["name", "branch"], page_size=100))
        except ERPNextAPIError as exc:
            raise CommandError(str(exc)) from exc

        if not companies:
            raise CommandError("ERPNext returned no companies.")
        if not any(row["name"] == options["branch_company"] for row in companies):
            raise CommandError(f"Unknown ERPNext branch company: {options['branch_company']}")

        with transaction.atomic():
            entities = self.sync_companies(
                organization, companies, options["fiscal_calendar"]
            )
            account_counts = self.sync_accounts(organization, entities, accounts)
            branch_counts = self.sync_branches(
                entities[options["branch_company"]], branches
            )
            cost_center_counts = self.sync_cost_centers(
                entities, cost_centers, branch_counts["branches"]
            )

        self.stdout.write(
            self.style.SUCCESS(
                "ERPNext master sync succeeded: "
                f"legal_entities={len(entities)} "
                f"group_accounts={account_counts['group_accounts']} "
                f"entity_accounts={account_counts['entity_accounts']} "
                f"branches={branch_counts['created_or_updated']} "
                f"cost_centers={cost_center_counts['created_or_updated']}"
            )
        )

    @staticmethod
    def sync_companies(organization, rows, calendar_code):
        calendar, _ = FiscalCalendar.objects.get_or_create(
            organization=organization,
            code=calendar_code,
            defaults={
                "name": f"ERPNext {calendar_code}",
                "timezone": "UTC",
            },
        )
        entities = {}
        for row in rows:
            currency_code = (row.get("default_currency") or "USD").upper()
            currency, _ = Currency.objects.get_or_create(
                code=currency_code,
                defaults={"name": currency_code},
            )
            entity_code = compact_code(f"ERP-{row.get('abbr') or row['name']}", limit=50)
            entity, _ = LegalEntity.objects.update_or_create(
                organization=organization,
                code=entity_code,
                defaults={
                    "legal_name": row["name"],
                    "short_name": row.get("abbr") or row["name"],
                    "functional_currency": currency,
                    "reporting_currency": currency,
                    "fiscal_calendar": calendar,
                    "valid_from": date(2026, 1, 1),
                },
            )
            entities[row["name"]] = entity
        return entities

    @staticmethod
    def sync_accounts(organization, entities, rows):
        rows = sorted(rows, key=lambda row: (row.get("company") or "", row.get("lft") or 0))
        group_by_source = {}
        entity_by_source = {}
        for row in rows:
            company = row.get("company")
            entity = entities.get(company)
            if not entity:
                continue
            source_name = row["name"]
            code = compact_code(source_name)
            defaults = {
                "name": row.get("account_name") or source_name,
                "account_type": account_type_for(row),
                "normal_balance": normal_balance_for(row),
                "is_posting_allowed": not bool(row.get("is_group")),
                "is_active": not bool(row.get("disabled")),
            }
            group, _ = GroupAccount.objects.update_or_create(
                organization=organization,
                code=code,
                defaults=defaults,
            )
            entity_account, _ = EntityAccount.objects.update_or_create(
                legal_entity=entity,
                code=code,
                defaults=defaults,
            )
            group_by_source[(company, source_name)] = group
            entity_by_source[(company, source_name)] = entity_account

        for row in rows:
            company = row.get("company")
            parent_name = row.get("parent_account")
            if not parent_name:
                continue
            group = group_by_source.get((company, row["name"]))
            parent_group = group_by_source.get((company, parent_name))
            entity_account = entity_by_source.get((company, row["name"]))
            parent_entity = entity_by_source.get((company, parent_name))
            if group and parent_group:
                group.parent = parent_group
                group.save(update_fields=["parent", "updated_at"])
            if entity_account and parent_entity:
                entity_account.parent = parent_entity
                entity_account.save(update_fields=["parent", "updated_at"])
        return {
            "group_accounts": len(group_by_source),
            "entity_accounts": len(entity_by_source),
        }

    @staticmethod
    def sync_branches(entity, rows):
        cities = {"AMM": "Amman", "IRB": "Irbid", "AQB": "Aqaba"}
        branches = {}
        for row in rows:
            source_name = row.get("branch") or row["name"]
            branch, _ = Branch.objects.update_or_create(
                legal_entity=entity,
                code=compact_code(source_name, limit=20),
                defaults={
                    "name": source_name,
                    "city": cities.get(source_name, source_name),
                    "timezone": "Asia/Amman",
                },
            )
            branches[source_name] = branch
        return {"created_or_updated": len(branches), "branches": branches}

    @staticmethod
    def sync_cost_centers(entities, rows, branches):
        objects = {}
        for row in sorted(rows, key=lambda item: (item.get("company") or "", item.get("lft") or 0)):
            entity = entities.get(row.get("company"))
            if not entity:
                continue
            source_name = row["name"]
            code = compact_code(row.get("cost_center_name") or source_name, limit=50)
            branch = branches.get(row.get("cost_center_name"))
            cost_center, _ = CostCenter.objects.update_or_create(
                legal_entity=entity,
                code=code,
                defaults={
                    "name": row.get("cost_center_name") or source_name,
                    "branch": branch if branch and branch.legal_entity_id == entity.id else None,
                    "is_active": not bool(row.get("disabled")),
                },
            )
            objects[(row.get("company"), source_name)] = cost_center

        for row in rows:
            cost_center = objects.get((row.get("company"), row["name"]))
            parent = objects.get((row.get("company"), row.get("parent_cost_center")))
            if cost_center and parent:
                cost_center.parent = parent
                cost_center.save(update_fields=["parent", "updated_at"])
        return {"created_or_updated": len(objects)}