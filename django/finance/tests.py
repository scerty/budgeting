from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from unittest.mock import patch

from .models import (
    AccountHierarchy,
    AccountHierarchyNode,
    AllocationRule,
    AllocationRuleLine,
    Branch,
    BudgetLine,
    BudgetPlan,
    BudgetVersion,
    CalculationRule,
    CalculationRuleDependency,
    CalculationRun,
    Department,
    DriverValue,
    Expense,
    ExchangeRate,
    FiscalPeriod,
    GroupAccount,
    ImportSource,
    IngestionIssue,
    IngestionRun,
    LegalEntity,
    JournalEntry,
    JournalEntryLine,
    NewCodeDiscovery,
    Organization,
    PlanningDriver,
    PlanningFact,
    PlanningSubmission,
    RawJournalLine,
    ReportColumn,
    ReportColumnModel,
    ReportColumnModelItem,
    ReportGroup,
    ReportTemplate,
    Role,
    Scenario,
    ScenarioBlend,
    ScenarioVersion,
    Supplier,
    UserProfile,
    UserOrgScope,
    WorkflowDefinition,
    WorkflowStep,
    Invoice,
    Currency,
    ConsolidationGroup,
    ConsolidationRun,
    ConsolidationScope,
    EliminationRule,
    IntercompanyPair,
)


class FinanceModelIntegrityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.get(code="DEMO")
        cls.entity = LegalEntity.objects.get(code="DEMO-JO")
        cls.currency = Currency.objects.get(code="USD")
        cls.period = FiscalPeriod.objects.get(code="2026")
        cls.group_account = GroupAccount.objects.get(code="600000")
        cls.branch = Branch.objects.create(
            code="TST",
            name="Test Branch",
            city="Amman",
            legal_entity=cls.entity,
        )
        cls.other_branch = Branch.objects.create(
            code="TST-2",
            name="Other Test Branch",
            city="Irbid",
            legal_entity=cls.entity,
        )
        cls.department = Department.objects.create(
            code="TST-OPS",
            name="Test Operations",
            branch=cls.branch,
            legal_entity=cls.entity,
        )

    def test_expense_rejects_branch_different_from_department(self):
        expense = Expense(
            department=self.department,
            branch=self.other_branch,
            legal_entity=self.entity,
            amount=Decimal("100.00"),
            currency="USD",
            currency_master=self.currency,
            expense_date="2026-01-01",
            description="Invalid scope",
        )

        with self.assertRaises(ValidationError):
            expense.full_clean()

    def test_budget_line_grain_rejects_duplicate_detail(self):
        plan = BudgetPlan.objects.create(
            organization=self.organization,
            code="TEST-PLAN",
            name="Test Plan",
            fiscal_calendar=self.entity.fiscal_calendar,
        )
        version = BudgetVersion.objects.create(
            plan=plan,
            code="BASE",
            name="Base",
            version_type="original",
        )
        line_values = {
            "version": version,
            "legal_entity": self.entity,
            "fiscal_period": self.period,
            "group_account": self.group_account,
            "amount": Decimal("1000.00"),
            "currency": self.currency,
        }
        BudgetLine.objects.create(**line_values)
        duplicate = BudgetLine(**line_values)

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_journal_entry_rejects_unbalanced_lines(self):
        entity_account = self.entity.entity_accounts.get(code="600000")
        entry = JournalEntry.objects.create(
            organization=self.organization,
            legal_entity=self.entity,
            fiscal_period=self.period,
            entry_number="TST-JE-001",
            entry_date="2026-01-15",
            currency=self.currency,
        )
        JournalEntryLine.objects.create(
            entry=entry,
            line_number=1,
            entity_account=entity_account,
            group_account=self.group_account,
            debit=Decimal("100.00"),
        )
        JournalEntryLine.objects.create(
            entry=entry,
            line_number=2,
            entity_account=entity_account,
            group_account=self.group_account,
            credit=Decimal("90.00"),
        )

        with self.assertRaises(ValidationError):
            entry.validate_balanced()

    def test_invoice_requires_matching_counterparty_and_totals(self):
        supplier = Supplier.objects.create(
            organization=self.organization,
            code="TST-SUPPLIER",
            name="Test Supplier",
        )
        invoice = Invoice(
            organization=self.organization,
            legal_entity=self.entity,
            direction="payable",
            supplier=supplier,
            invoice_number="TST-INV-001",
            invoice_date="2026-01-15",
            currency=self.currency,
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("15.00"),
            total_amount=Decimal("115.00"),
        )
        invoice.full_clean()

        invalid_invoice = Invoice(
            organization=self.organization,
            legal_entity=self.entity,
            direction="receivable",
            supplier=supplier,
            invoice_number="TST-INV-002",
            invoice_date="2026-01-15",
            currency=self.currency,
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("15.00"),
            total_amount=Decimal("115.00"),
        )
        with self.assertRaises(ValidationError):
            invalid_invoice.full_clean()

    def test_allocation_rule_requires_complete_distribution(self):
        rule = AllocationRule.objects.create(
            organization=self.organization,
            code="TST-ALLOC",
            name="Test allocation",
            basis="manual",
        )
        AllocationRuleLine.objects.create(
            rule=rule,
            target_legal_entity=self.entity,
            allocation_percentage=Decimal("60.0000"),
        )

        with self.assertRaises(ValidationError):
            rule.validate_percentages()

    def test_exchange_rate_rejects_same_currency(self):
        exchange_rate = ExchangeRate(
            from_currency=self.currency,
            to_currency=self.currency,
            rate_date="2026-01-15",
            rate=Decimal("1.000000000000"),
        )

        with self.assertRaises(ValidationError):
            exchange_rate.full_clean()

    def test_ingestion_source_must_match_organization(self):
        source = ImportSource.objects.create(
            organization=self.organization,
            name="Test ERP",
            protocol="csv",
        )
        other_organization = Organization.objects.create(
            code="OTHER",
            legal_name="Other Organization",
            display_name="Other Organization",
        )
        run = IngestionRun(
            organization=other_organization,
            import_source=source,
            source_system="test",
            source_entity="gl",
            strategy="snapshot",
        )

        with self.assertRaises(ValidationError):
            run.full_clean()

    def test_raw_journal_line_requires_one_sided_amount(self):
        run = IngestionRun.objects.create(
            organization=self.organization,
            source_system="test",
            source_entity="gl",
            strategy="snapshot",
        )
        line = RawJournalLine(
            ingestion_run=run,
            source_system="test",
            source_entity="gl",
            source_record_id="DOC-1",
            source_line_id="1",
            posting_date="2026-01-15",
            source_account_code="600000",
            currency="USD",
            debit_amount=Decimal("100.00"),
            credit_amount=Decimal("10.00"),
            record_hash="raw-gl-1",
        )

        with self.assertRaises(ValidationError):
            line.full_clean()

    def test_discovered_code_must_match_ingestion_organization(self):
        run = IngestionRun.objects.create(
            organization=self.organization,
            source_system="test",
            source_entity="gl",
            strategy="snapshot",
        )
        other_organization = Organization.objects.create(
            code="OTHER-DISCOVERY",
            legal_name="Other Discovery Organization",
            display_name="Other Discovery Organization",
        )
        discovery = NewCodeDiscovery(
            ingestion_run=run,
            organization=other_organization,
            code_type="account",
            code="999999",
        )

        with self.assertRaises(ValidationError):
            discovery.full_clean()

    def test_account_can_appear_in_multiple_hierarchies(self):
        legal_hierarchy = AccountHierarchy.objects.create(
            organization=self.organization,
            code="LEGAL",
            name="Legal P&L",
            is_default=True,
        )
        management_hierarchy = AccountHierarchy.objects.create(
            organization=self.organization,
            code="MANAGEMENT",
            name="Management P&L",
        )
        AccountHierarchyNode.objects.create(
            hierarchy=legal_hierarchy,
            node_code="LEGAL-600000",
            group_account=self.group_account,
        )
        AccountHierarchyNode.objects.create(
            hierarchy=management_hierarchy,
            node_code="MGMT-600000",
            group_account=self.group_account,
        )

        self.assertEqual(
            self.group_account.hierarchy_nodes.filter(
                hierarchy__in=[legal_hierarchy, management_hierarchy]
            ).count(),
            2,
        )

    def test_account_hierarchy_rejects_invalid_subtotal(self):
        hierarchy = AccountHierarchy.objects.create(
            organization=self.organization,
            code="INVALID",
            name="Invalid hierarchy",
        )
        node = AccountHierarchyNode(
            hierarchy=hierarchy,
            is_subtotal=True,
            group_account=self.group_account,
        )

        with self.assertRaises(ValidationError):
            node.full_clean()

    def test_consolidation_run_and_scope_match_organization(self):
        child_entity = LegalEntity.objects.create(
            organization=self.organization,
            code="DEMO-CHILD",
            legal_name="Demo Child Entity",
            functional_currency=self.currency,
            reporting_currency=self.currency,
            fiscal_calendar=self.entity.fiscal_calendar,
        )
        group = ConsolidationGroup.objects.create(
            organization=self.organization,
            code="DEMO-GROUP",
            name="Demo Group",
            parent_entity=self.entity,
            reporting_currency=self.currency,
        )
        scope = ConsolidationScope(
            group=group,
            legal_entity=child_entity,
        )
        scope.full_clean()
        scope.save()
        run = ConsolidationRun(
            group=group,
            fiscal_period=self.period,
            data_set="actuals",
        )
        run.full_clean()
        run.save()
        self.assertEqual(run.group_id, group.id)

    def test_intercompany_pair_and_rule_match_organization(self):
        child_entity = LegalEntity.objects.create(
            organization=self.organization,
            code="DEMO-IC",
            legal_name="Demo Intercompany Entity",
            functional_currency=self.currency,
            reporting_currency=self.currency,
            fiscal_calendar=self.entity.fiscal_calendar,
        )
        pair = IntercompanyPair(
            organization=self.organization,
            entity_a=self.entity,
            entity_b=child_entity,
        )
        pair.full_clean()
        rule = EliminationRule(
            organization=self.organization,
            code="IC-REV-COST",
            name="Intercompany revenue and cost",
            account_at_entity_a=self.group_account,
            account_at_entity_b=self.group_account,
        )
        rule.full_clean()

    def test_scenario_blend_requires_source_and_rejects_same_priority_overlap(self):
        scenario = Scenario.objects.create(
            organization=self.organization,
            code="TST-FORECAST",
            name="Test forecast",
            scenario_type="forecast",
        )
        result_version = ScenarioVersion.objects.create(
            scenario=scenario,
            code="V1",
            name="Forecast version 1",
        )
        invalid_planning_component = ScenarioBlend(
            result_version=result_version,
            source_kind="planning",
            fiscal_period_from=self.period,
            fiscal_period_to=self.period,
        )
        with self.assertRaises(ValidationError):
            invalid_planning_component.full_clean()

        actual_component = ScenarioBlend(
            result_version=result_version,
            source_kind="actuals",
            fiscal_period_from=self.period,
            fiscal_period_to=self.period,
        )
        actual_component.full_clean()
        actual_component.save()

        overlapping_component = ScenarioBlend(
            result_version=result_version,
            source_kind="actuals",
            fiscal_period_from=self.period,
            fiscal_period_to=self.period,
        )
        with self.assertRaises(ValidationError):
            overlapping_component.full_clean()

    def test_driver_values_can_be_global_or_scenario_scoped(self):
        scenario = Scenario.objects.create(
            organization=self.organization,
            code="TST-BUDGET",
            name="Test budget",
            scenario_type="budget",
        )
        scenario_version = ScenarioVersion.objects.create(
            scenario=scenario,
            code="V1",
            name="Budget version 1",
        )
        driver = PlanningDriver.objects.create(
            organization=self.organization,
            code="HEADCOUNT",
            name="Headcount",
            unit="people",
        )
        global_value = DriverValue(
            driver=driver,
            fiscal_period=self.period,
            value=Decimal("10"),
        )
        global_value.full_clean()
        global_value.save()
        scenario_value = DriverValue(
            driver=driver,
            scenario_version=scenario_version,
            fiscal_period=self.period,
            value=Decimal("12"),
        )
        scenario_value.full_clean()
        scenario_value.save()
        self.assertEqual(driver.values.count(), 2)

    def test_user_scope_rejects_role_from_another_organization(self):
        user = get_user_model().objects.create_user(
            username="scope-user",
            password="test-password",
        )
        other_organization = Organization.objects.create(
            code="OTHER-SCOPE",
            legal_name="Other Scope Organization",
            display_name="Other Scope Organization",
        )
        other_role = Role.objects.create(
            organization=other_organization,
            code="VIEWER",
            name="Viewer",
        )
        scope = UserOrgScope(
            user=user,
            role=other_role,
            organization=self.organization,
        )
        with self.assertRaises(ValidationError):
            scope.full_clean()

    def test_user_profile_rejects_inactive_default_organization(self):
        user = get_user_model().objects.create_user(
            username="profile-user",
            password="test-password",
        )
        inactive_organization = Organization.objects.create(
            code="INACTIVE-PROFILE",
            legal_name="Inactive Profile Organization",
            display_name="Inactive Profile Organization",
            status="inactive",
        )
        profile = UserProfile(
            user=user,
            default_organization=inactive_organization,
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_planning_fact_matches_calculation_run_scenario(self):
        scenario = Scenario.objects.create(
            organization=self.organization,
            code="TST-FACT",
            name="Fact scenario",
            scenario_type="forecast",
        )
        scenario_version = ScenarioVersion.objects.create(
            scenario=scenario,
            code="V1",
            name="Fact scenario version 1",
        )
        run = CalculationRun.objects.create(
            organization=self.organization,
            scenario_version=scenario_version,
        )
        fact = PlanningFact(
            calculation_run=run,
            scenario_version=scenario_version,
            fiscal_period=self.period,
            legal_entity=self.entity,
            group_account=self.group_account,
            source_kind="calculated",
            amount=Decimal("125.00"),
            currency=self.currency,
        )
        fact.full_clean()
        fact.save()
        duplicate = PlanningFact(
            calculation_run=run,
            scenario_version=scenario_version,
            fiscal_period=self.period,
            legal_entity=self.entity,
            group_account=self.group_account,
            source_kind="calculated",
            amount=Decimal("130.00"),
            currency=self.currency,
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_calculation_engine_is_safe_and_detects_cycles(self):
        from .planning import evaluate_calculation_rule, evaluate_calculation_rules

        rule = CalculationRule(
            organization=self.organization,
            code="GROSS_COST",
            name="Gross cost",
            expression="revenue * growth",
            input_keys=["revenue", "growth"],
        )
        self.assertEqual(
            evaluate_calculation_rule(rule, {"revenue": 100, "growth": "1.25"}),
            Decimal("125.000000"),
        )
        unsafe_rule = CalculationRule(
            organization=self.organization,
            code="UNSAFE",
            name="Unsafe",
            expression="__import__('os')",
        )
        with self.assertRaises(ValidationError):
            evaluate_calculation_rule(unsafe_rule, {})

        first_rule = CalculationRule.objects.create(
            organization=self.organization,
            code="RULE-A",
            name="Rule A",
            expression="base + 1",
            input_keys=["base"],
        )
        second_rule = CalculationRule.objects.create(
            organization=self.organization,
            code="RULE-B",
            name="Rule B",
            expression="RULE-A + 1",
            input_keys=["RULE-A"],
        )
        CalculationRuleDependency.objects.create(rule=first_rule, depends_on=second_rule)
        CalculationRuleDependency.objects.create(rule=second_rule, depends_on=first_rule)
        with self.assertRaises(ValidationError):
            evaluate_calculation_rules([first_rule, second_rule], {"base": 1})

    def test_report_template_and_group_must_share_organization(self):
        report_group = ReportGroup.objects.create(
            organization=self.organization,
            name="Financial Statements",
        )
        hierarchy = AccountHierarchy.objects.create(
            organization=self.organization,
            code="REPORTING",
            name="Reporting hierarchy",
        )
        user = get_user_model().objects.create_user(
            username="report-owner",
            password="test-password",
        )
        template = ReportTemplate(
            organization=self.organization,
            name="P&L",
            group=report_group,
            account_hierarchy=hierarchy,
            created_by=user,
        )
        template.full_clean()

        other_organization = Organization.objects.create(
            code="OTHER-REPORT",
            legal_name="Other Report Organization",
            display_name="Other Report Organization",
        )
        other_group = ReportGroup.objects.create(
            organization=other_organization,
            name="Other Group",
        )
        invalid_template = ReportTemplate(
            organization=self.organization,
            name="Invalid P&L",
            group=other_group,
            account_hierarchy=hierarchy,
            created_by=user,
        )
        with self.assertRaises(ValidationError):
            invalid_template.full_clean()

    def test_report_columns_enforce_source_and_variance_rules(self):
        scenario = Scenario.objects.create(
            organization=self.organization,
            code="TST-REPORT-SCENARIO",
            name="Report scenario",
            scenario_type="forecast",
        )
        scenario_version = ScenarioVersion.objects.create(
            scenario=scenario,
            code="V1",
            name="Report scenario version",
        )
        hierarchy = AccountHierarchy.objects.create(
            organization=self.organization,
            code="REPORT-COLUMNS",
            name="Report columns hierarchy",
        )
        user = get_user_model().objects.create_user(
            username="column-owner",
            password="test-password",
        )
        template = ReportTemplate.objects.create(
            organization=self.organization,
            name="Column report",
            account_hierarchy=hierarchy,
            created_by=user,
        )
        actual_column = ReportColumn(
            template=template,
            sort_order=1,
            label="Actuals",
            data_type="actuals",
        )
        actual_column.full_clean()
        actual_column.save()
        scenario_column = ReportColumn(
            template=template,
            sort_order=2,
            label="Forecast",
            data_type="scenario",
            scenario_version=scenario_version,
        )
        scenario_column.full_clean()
        scenario_column.save()
        variance_column = ReportColumn(
            template=template,
            sort_order=3,
            label="Variance",
            data_type="variance",
            variance_base_column=actual_column,
            variance_compare_column=scenario_column,
        )
        variance_column.full_clean()
        variance_column.save()
        from .reporting import build_report_column_specs

        report_specs = build_report_column_specs(template)
        self.assertEqual([spec["source"]["kind"] for spec in report_specs], [
            "actuals",
            "scenario",
            "variance",
        ])
        self.assertEqual(report_specs[2]["source"]["base_column_id"], actual_column.id)

        invalid_scenario_column = ReportColumn(
            template=template,
            sort_order=4,
            label="Invalid actuals",
            data_type="actuals",
            scenario_version=scenario_version,
        )
        with self.assertRaises(ValidationError):
            invalid_scenario_column.full_clean()

        column_model = ReportColumnModel.objects.create(
            organization=self.organization,
            name="Monthly columns",
        )
        mixed_item = ReportColumnModelItem(
            column_model=column_model,
            sort_order=1,
            label_prefix="Outlook",
            data_type="mixed",
            scenario_version=scenario_version,
        )
        with self.assertRaises(ValidationError):
            mixed_item.full_clean()

    def test_planning_submission_matches_workflow_and_scenario_organization(self):
        scenario = Scenario.objects.create(
            organization=self.organization,
            code="TST-SUBMISSION",
            name="Submission scenario",
            scenario_type="budget",
        )
        scenario_version = ScenarioVersion.objects.create(
            scenario=scenario,
            code="V1",
            name="Submission version",
        )
        role = Role.objects.create(
            organization=self.organization,
            code="APPROVER",
            name="Approver",
        )
        workflow = WorkflowDefinition.objects.create(
            organization=self.organization,
            code="BUDGET-SUBMIT",
            name="Budget submission",
            target_type="planning_submission",
        )
        step = WorkflowStep(
            workflow=workflow,
            sequence=1,
            name="Finance review",
            required_role="APPROVER",
            required_role_ref=role,
        )
        step.full_clean()
        step.save()
        submission = PlanningSubmission(
            organization=self.organization,
            workflow=workflow,
            scenario_version=scenario_version,
            legal_entity=self.entity,
            current_step=step,
            status="submitted",
        )
        submission.full_clean()
        submission.save()

        other_organization = Organization.objects.create(
            code="OTHER-SUBMISSION",
            legal_name="Other Submission Organization",
            display_name="Other Submission Organization",
        )
        invalid_submission = PlanningSubmission(
            organization=other_organization,
            workflow=workflow,
            scenario_version=scenario_version,
        )
        with self.assertRaises(ValidationError):
            invalid_submission.full_clean()


class ERPNextIngestionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.get(code="DEMO")

    def test_gl_entry_import_is_idempotent_and_keeps_source_payload(self):
        row = {
            "name": "GL-TEST-001",
            "company": "Demo Company",
            "posting_date": "2026-01-15",
            "transaction_date": "2026-01-15",
            "account": "600000 - Operating Expense - DC",
            "account_currency": "USD",
            "debit": 125,
            "credit": 0,
            "is_cancelled": 0,
            "voucher_type": "Journal Entry",
            "voucher_no": "ACC-JV-TEST-001",
            "remarks": "ERPNext test line",
            "creation": "2026-01-15 10:00:00",
            "modified": "2026-01-15 10:00:00",
        }

        class FakeClient:
            def __init__(self, **kwargs):
                pass

            def login(self):
                pass

            def iter_resource(self, *args, **kwargs):
                yield row

        with patch("finance.management.commands.ingest_erpnext.ERPNextClient", FakeClient):
            call_command(
                "ingest_erpnext",
                organization="DEMO",
                base_url="http://erpnext.test",
                password="test-password",
            )
            call_command(
                "ingest_erpnext",
                organization="DEMO",
                base_url="http://erpnext.test",
                password="test-password",
            )

        line = RawJournalLine.objects.get(source_line_id="GL-TEST-001")
        self.assertEqual(RawJournalLine.objects.count(), 1)
        self.assertEqual(line.debit_amount, Decimal("125.00"))
        self.assertEqual(line.credit_amount, Decimal("0.00"))
        self.assertEqual(line.source_payload, row)
        self.assertEqual(len(line.record_hash), 64)
        runs = list(IngestionRun.objects.filter(source_system="erpnext").order_by("started_at"))
        self.assertEqual([(run.records_inserted, run.records_updated) for run in runs], [(1, 0), (0, 1)])
        self.assertTrue(all(run.status == "succeeded" for run in runs))