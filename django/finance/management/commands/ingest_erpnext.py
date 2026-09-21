import hashlib
import json
import os
from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from finance.ingestion.erpnext import ERPNextClient
from finance.models import (
    ImportProtocol,
    ImportSource,
    IngestionIssue,
    IngestionIssueSeverity,
    IngestionRun,
    IngestionRunStatus,
    IngestionStrategy,
    Organization,
    RawJournalLine,
)


GL_ENTRY_FIELDS = [
    "name",
    "company",
    "posting_date",
    "transaction_date",
    "account",
    "account_currency",
    "transaction_currency",
    "cost_center",
    "project",
    "party",
    "party_type",
    "voucher_type",
    "voucher_no",
    "voucher_detail_no",
    "remarks",
    "debit",
    "credit",
    "is_cancelled",
    "creation",
    "modified",
]


def parse_date(value, field_name):
    if not value:
        raise ValueError(f"{field_name} is required")
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}: {value}") from exc


def parse_datetime(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return timezone.make_aware(parsed, timezone=dt_timezone.utc)
    return parsed


def parse_amount(value):
    try:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid amount: {value}") from exc


def parse_bool(value):
    return value is True or value in (1, "1", "true", "True")


def payload_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class Command(BaseCommand):
    help = "Import ERPNext GL Entry rows into RawJournalLine."

    def add_arguments(self, parser):
        parser.add_argument("--organization", default="DEMO")
        parser.add_argument(
            "--base-url",
            default=os.environ.get("ERPNEXT_URL", "http://host.docker.internal:18080"),
        )
        parser.add_argument("--username", default=os.environ.get("ERPNEXT_USER", "Administrator"))
        parser.add_argument("--password", default=os.environ.get("ERPNEXT_PASSWORD"))
        parser.add_argument("--page-size", type=int, default=100)
        parser.add_argument("--currency", default="USD")
        parser.add_argument("--from-date")
        parser.add_argument("--to-date")
        parser.add_argument("--include-cancelled", action="store_true")

    def handle(self, *args, **options):
        if not options["password"]:
            raise CommandError("Pass --password or set ERPNEXT_PASSWORD.")
        if options["page_size"] < 1 or options["page_size"] > 1000:
            raise CommandError("--page-size must be between 1 and 1000.")

        try:
            organization = Organization.objects.get(code=options["organization"])
        except Organization.DoesNotExist as exc:
            raise CommandError(f"Unknown Django organization: {options['organization']}") from exc

        source_config = {
            "base_url": options["base_url"],
            "doctype": "GL Entry",
            "page_size": options["page_size"],
            "cancellation_policy": "include" if options["include_cancelled"] else "active_only",
        }
        import_source, created = ImportSource.objects.get_or_create(
            organization=organization,
            name="ERPNext GL Entry",
            defaults={
                "protocol": ImportProtocol.REST_API,
                "configuration": source_config,
            },
        )
        if not created:
            import_source.protocol = ImportProtocol.REST_API
            import_source.configuration = source_config
            import_source.save(update_fields=["protocol", "configuration", "updated_at"])

        ingestion_run = IngestionRun.objects.create(
            organization=organization,
            import_source=import_source,
            source_system="erpnext",
            source_entity="GL Entry",
            strategy=IngestionStrategy.SNAPSHOT,
            external_run_id=f"erpnext-gl-{uuid4().hex}",
        )
        counters = {"read": 0, "inserted": 0, "updated": 0, "skipped": 0, "failed": 0}
        filters = []
        if not options["include_cancelled"]:
            filters.append(["is_cancelled", "=", 0])
        if options["from_date"]:
            filters.append(["posting_date", ">=", options["from_date"]])
        if options["to_date"]:
            filters.append(["posting_date", "<=", options["to_date"]])

        try:
            client = ERPNextClient(
                base_url=options["base_url"],
                username=options["username"],
                password=options["password"],
            )
            client.login()
            for row in client.iter_resource(
                "GL Entry",
                fields=GL_ENTRY_FIELDS,
                filters=filters,
                page_size=options["page_size"],
            ):
                counters["read"] += 1
                if parse_bool(row.get("is_cancelled")) and not options["include_cancelled"]:
                    counters["skipped"] += 1
                    continue
                try:
                    created_row = self.upsert_row(
                        ingestion_run,
                        row,
                        fallback_currency=options["currency"],
                        include_cancelled=options["include_cancelled"],
                    )
                    counters["inserted" if created_row else "updated"] += 1
                except (KeyError, TypeError, ValueError) as exc:
                    counters["failed"] += 1
                    self.record_issue(ingestion_run, row, str(exc), counters["read"])
        except Exception as exc:
            self.finish_run(ingestion_run, counters, IngestionRunStatus.FAILED, str(exc))
            if isinstance(exc, CommandError):
                raise
            raise CommandError(str(exc)) from exc

        status = IngestionRunStatus.PARTIAL if counters["failed"] else IngestionRunStatus.SUCCEEDED
        self.finish_run(ingestion_run, counters, status)
        self.stdout.write(
            self.style.SUCCESS(
                f"ERPNext GL import {status}: read={counters['read']} "
                f"inserted={counters['inserted']} updated={counters['updated']} "
                f"skipped={counters['skipped']} failed={counters['failed']} "
                f"run={ingestion_run.external_run_id}"
            )
        )

    @staticmethod
    @transaction.atomic
    def upsert_row(ingestion_run, row, fallback_currency, include_cancelled):
        source_line_id = str(row["name"])
        source_record_id = str(row.get("voucher_no") or source_line_id)
        debit_amount = parse_amount(row.get("debit"))
        credit_amount = parse_amount(row.get("credit"))
        if debit_amount < 0 or credit_amount < 0:
            raise ValueError("debit and credit must not be negative")
        if (debit_amount > 0) == (credit_amount > 0):
            raise ValueError("GL Entry must contain exactly one positive side")

        account = str(row.get("account") or "").strip()
        if not account:
            raise ValueError("account is required")
        is_cancelled = parse_bool(row.get("is_cancelled"))
        defaults = {
            "ingestion_run": ingestion_run,
            "source_legal_entity_code": str(row.get("company") or ""),
            "document_number": str(row.get("voucher_no") or ""),
            "document_date": parse_date(row.get("transaction_date"), "transaction_date")
            if row.get("transaction_date")
            else None,
            "description": str(row.get("remarks") or row.get("voucher_type") or "")[:255],
            "source_account_code": account,
            "source_cost_center_code": str(row.get("cost_center") or ""),
            "source_project_code": str(row.get("project") or ""),
            "source_counterparty_code": str(row.get("party") or ""),
            "currency": str(
                row.get("transaction_currency") or row.get("account_currency") or fallback_currency
            ).upper(),
            "debit_amount": debit_amount,
            "credit_amount": credit_amount,
            "source_created_at": parse_datetime(row.get("creation")),
            "source_updated_at": parse_datetime(row.get("modified")),
            "record_hash": payload_hash(row),
            "is_deleted": is_cancelled if include_cancelled else False,
            "source_payload": row,
        }
        _, created = RawJournalLine.objects.update_or_create(
            source_system="erpnext",
            source_entity="GL Entry",
            source_record_id=source_record_id,
            source_line_id=source_line_id,
            defaults={
                **defaults,
                "posting_date": parse_date(row.get("posting_date"), "posting_date"),
            },
        )
        return created

    @staticmethod
    def record_issue(ingestion_run, row, message, row_number):
        IngestionIssue.objects.create(
            ingestion_run=ingestion_run,
            severity=IngestionIssueSeverity.ERROR,
            source_entity="GL Entry",
            source_record_id=str(row.get("voucher_no") or row.get("name") or ""),
            source_line_id=str(row.get("name") or ""),
            row_number=row_number,
            code="INVALID_GL_ENTRY",
            message=message,
            details=row,
        )

    @staticmethod
    def finish_run(ingestion_run, counters, status, error_message=""):
        ingestion_run.status = status
        ingestion_run.finished_at = timezone.now()
        ingestion_run.records_read = counters["read"]
        ingestion_run.records_inserted = counters["inserted"]
        ingestion_run.records_updated = counters["updated"]
        ingestion_run.records_skipped = counters["skipped"]
        ingestion_run.records_failed = counters["failed"]
        ingestion_run.error_message = error_message
        ingestion_run.save(
            update_fields=[
                "status",
                "finished_at",
                "records_read",
                "records_inserted",
                "records_updated",
                "records_skipped",
                "records_failed",
                "error_message",
                "updated_at",
            ]
        )