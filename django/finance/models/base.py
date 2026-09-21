from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class AccountType(models.TextChoices):
    ASSET = "asset", "Asset"
    LIABILITY = "liability", "Liability"
    EQUITY = "equity", "Equity"
    REVENUE = "revenue", "Revenue"
    COST_OF_SALES = "cost_of_sales", "Cost of sales"
    OPERATING_EXPENSE = "operating_expense", "Operating expense"
    OTHER_INCOME = "other_income", "Other income"
    OTHER_EXPENSE = "other_expense", "Other expense"
    TAX = "tax", "Tax"
    STATISTICAL = "statistical", "Statistical"

class NormalBalance(models.TextChoices):
    DEBIT = "debit", "Debit"
    CREDIT = "credit", "Credit"

class LifecycleStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"

class ConsolidationMethod(models.TextChoices):
    FULL = "full", "Full consolidation"
    EQUITY = "equity", "Equity method"
    PROPORTIONAL = "proportional", "Proportional consolidation"
    EXCLUDED = "excluded", "Excluded"

class MappingType(models.TextChoices):
    ONE_TO_ONE = "one_to_one", "One to one"
    MANY_TO_ONE = "many_to_one", "Many to one"
    ONE_TO_MANY = "one_to_many", "One to many"
    MANUAL_ADJUSTMENT = "manual_adjustment", "Manual adjustment"
    UNMAPPED = "unmapped", "Unmapped"

class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    BLOCKED = "blocked", "Blocked"

class BudgetStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CLOSED = "closed", "Closed"

class BudgetVersionType(models.TextChoices):
    ORIGINAL = "original", "Original budget"
    REVISED = "revised", "Revised budget"
    FORECAST = "forecast", "Forecast"

class ScenarioType(models.TextChoices):
    BUDGET = "budget", "Budget"
    FORECAST = "forecast", "Forecast"
    ROLLING_FORECAST = "rolling_forecast", "Rolling forecast"
    BEST_CASE = "best_case", "Best case"
    WORST_CASE = "worst_case", "Worst case"
    SIMULATION = "simulation", "Simulation"

class ScenarioStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"

class ScenarioVersionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    IN_REVIEW = "in_review", "In review"
    APPROVED = "approved", "Approved"
    LOCKED = "locked", "Locked"
    ARCHIVED = "archived", "Archived"

class ScenarioBlendSource(models.TextChoices):
    ACTUALS = "actuals", "Actuals"
    PLANNING = "planning", "Planning scenario"

class CalculationRuleType(models.TextChoices):
    DRIVER = "driver", "Driver"
    ALLOCATION = "allocation", "Allocation"
    ACCOUNT_TO_ACCOUNT = "account_to_account", "Account to account"
    GROWTH = "growth", "Growth"
    SPREAD = "spread", "Spread"
    FX = "fx", "Foreign exchange"

class CalculationRunStatus(models.TextChoices):
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"

class PlanningFactSource(models.TextChoices):
    INPUT = "input", "Manual input"
    CALCULATED = "calculated", "Calculated"
    ALLOCATED = "allocated", "Allocated"
    IMPORTED = "imported", "Imported"

class ReportColumnSourceType(models.TextChoices):
    ACTUALS = "actuals", "Actuals"
    SCENARIO = "scenario", "Scenario/version"
    MIXED = "mixed", "Actuals plus scenario"

class ReportColumnType(models.TextChoices):
    ACTUALS = "actuals", "Actuals"
    SCENARIO = "scenario", "Scenario/version"
    VARIANCE = "variance", "Variance"
    MIXED = "mixed", "Actuals plus scenario"

class ReportColumnModelType(models.TextChoices):
    ANALYSIS = "analysis", "Analysis report"
    MONTHLY = "monthly", "Monthly report"

class SubmissionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    IN_REVIEW = "in_review", "In review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"

class IngestionStrategy(models.TextChoices):
    CURSOR = "cursor", "Cursor"
    SNAPSHOT = "snapshot", "Snapshot"
    APPEND_ONLY = "append_only", "Append only"
    FULL_REFRESH = "full_refresh", "Full refresh"

class IngestionRunStatus(models.TextChoices):
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    PARTIAL = "partial", "Partial"

class ImportProtocol(models.TextChoices):
    CSV_UPLOAD = "csv", "CSV/Excel upload"
    SFTP = "sftp", "SFTP file drop"
    REST_API = "api", "REST API"
    DB_LINK = "db", "Direct database link"

class DiscoveryCodeType(models.TextChoices):
    ACCOUNT = "account", "Account"
    LEGAL_ENTITY = "legal_entity", "Legal entity"
    BRANCH = "branch", "Branch"
    DEPARTMENT = "department", "Department"
    COST_CENTER = "cost_center", "Cost center"
    PROFIT_CENTER = "profit_center", "Profit center"
    BUSINESS_UNIT = "business_unit", "Business unit"
    PROJECT = "project", "Project"

class DiscoveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    LINKED = "linked", "Linked"
    CREATED = "created", "Created"
    REJECTED = "rejected", "Rejected"

class IngestionIssueSeverity(models.TextChoices):
    WARNING = "warning", "Warning"
    ERROR = "error", "Error"

class ExchangeRateType(models.TextChoices):
    SPOT = "spot", "Spot"
    AVERAGE = "average", "Average"
    CLOSING = "closing", "Closing"
    BUDGET = "budget", "Budget"

class TaxType(models.TextChoices):
    VAT = "vat", "VAT"
    SALES = "sales", "Sales tax"
    WITHHOLDING = "withholding", "Withholding tax"
    OTHER = "other", "Other"

class InvoiceDirection(models.TextChoices):
    PAYABLE = "payable", "Accounts payable"
    RECEIVABLE = "receivable", "Accounts receivable"

class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    APPROVED = "approved", "Approved"
    POSTED = "posted", "Posted"
    PAID = "paid", "Paid"
    VOID = "void", "Void"

class PaymentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    POSTED = "posted", "Posted"
    RECONCILED = "reconciled", "Reconciled"
    VOID = "void", "Void"

class PlanningValueType(models.TextChoices):
    NUMBER = "number", "Number"
    PERCENTAGE = "percentage", "Percentage"
    CURRENCY = "currency", "Currency"
    TEXT = "text", "Text"

class AllocationBasis(models.TextChoices):
    EQUAL = "equal", "Equal"
    HEADCOUNT = "headcount", "Headcount"
    REVENUE = "revenue", "Revenue"
    EXPENSE = "expense", "Expense"
    MANUAL = "manual", "Manual"

class AllocationRuleStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    APPROVED = "approved", "Approved"
    INACTIVE = "inactive", "Inactive"

class EncumbranceStatus(models.TextChoices):
    OPEN = "open", "Open"
    PARTIALLY_RELEASED = "partially_released", "Partially released"
    RELEASED = "released", "Released"
    CONVERTED = "converted", "Converted to actual"
    CANCELLED = "cancelled", "Cancelled"

class ApprovalStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CANCELLED = "cancelled", "Cancelled"

class ApprovalActionType(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    COMMENTED = "commented", "Commented"
    CANCELLED = "cancelled", "Cancelled"

class JournalEntryStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    POSTED = "posted", "Posted"
    VOID = "void", "Void"

class ConsolidationDataSet(models.TextChoices):
    ACTUALS = "actuals", "Actuals"
    PLANNING = "planning", "Planning scenario"

class ConsolidationRunStatus(models.TextChoices):
    RUNNING = "running", "Running"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"

class IntercompanyMatchStatus(models.TextChoices):
    MATCHED = "matched", "Matched"
    PROBLEM = "problem", "Amount mismatch"
    UNKNOWN = "unknown", "Counterpart not found"

__all__ = ['TimeStampedModel', 'AccountType', 'NormalBalance', 'LifecycleStatus', 'ConsolidationMethod', 'MappingType', 'ReviewStatus', 'BudgetStatus', 'BudgetVersionType', 'ScenarioType', 'ScenarioStatus', 'ScenarioVersionStatus', 'ScenarioBlendSource', 'CalculationRuleType', 'CalculationRunStatus', 'PlanningFactSource', 'ReportColumnSourceType', 'ReportColumnType', 'ReportColumnModelType', 'SubmissionStatus', 'IngestionStrategy', 'IngestionRunStatus', 'ImportProtocol', 'DiscoveryCodeType', 'DiscoveryStatus', 'IngestionIssueSeverity', 'ExchangeRateType', 'TaxType', 'InvoiceDirection', 'InvoiceStatus', 'PaymentStatus', 'PlanningValueType', 'AllocationBasis', 'AllocationRuleStatus', 'EncumbranceStatus', 'ApprovalStatus', 'ApprovalActionType', 'JournalEntryStatus', 'ConsolidationDataSet', 'ConsolidationRunStatus', 'IntercompanyMatchStatus']
