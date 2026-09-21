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


class Encumbrance(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="encumbrances"
    )
    legal_entity = models.ForeignKey(
        LegalEntity, on_delete=models.PROTECT, related_name="encumbrances"
    )
    budget_version = models.ForeignKey(
        BudgetVersion,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="encumbrances",
    )
    fiscal_period = models.ForeignKey(
        FiscalPeriod, on_delete=models.PROTECT, related_name="encumbrances"
    )
    group_account = models.ForeignKey(
        GroupAccount, on_delete=models.PROTECT, related_name="encumbrances"
    )
    entity_account = models.ForeignKey(
        EntityAccount,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="encumbrances",
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="encumbrances"
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="encumbrances",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="encumbrances",
    )
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.PROTECT, related_name="encumbrances"
    )
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="encumbrances"
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(
        max_length=24, choices=EncumbranceStatus.choices, default=EncumbranceStatus.OPEN
    )
    source_system = models.CharField(max_length=80)
    source_entity = models.CharField(max_length=120)
    source_record_id = models.CharField(max_length=160)
    record_hash = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["fiscal_period_id", "legal_entity_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "source_entity", "source_record_id"],
                name="uniq_encumbrance_source_record",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0), name="encumbrance_amount_positive"
            ),
        ]

    def clean(self):
        if self.legal_entity.organization_id != self.organization_id:
            raise ValidationError("Encumbrance entity must belong to the organization.")
        if self.fiscal_period.calendar_id != self.legal_entity.fiscal_calendar_id:
            raise ValidationError("Encumbrance period must use the entity fiscal calendar.")
        if self.group_account.organization_id != self.organization_id:
            raise ValidationError("Encumbrance account must belong to the organization.")
        if self.entity_account_id and self.entity_account.legal_entity_id != self.legal_entity_id:
            raise ValidationError("Encumbrance local account must belong to the entity.")
        if self.budget_version_id and self.budget_version.plan.organization_id != self.organization_id:
            raise ValidationError("Encumbrance budget version must belong to the organization.")

class WorkflowDefinition(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="workflow_definitions"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=160)
    target_type = models.CharField(max_length=80)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_workflow_definition_code_org"
            ),
        ]

class WorkflowStep(TimeStampedModel):
    workflow = models.ForeignKey(
        WorkflowDefinition, on_delete=models.CASCADE, related_name="steps"
    )
    sequence = models.PositiveIntegerField()
    name = models.CharField(max_length=120)
    required_role = models.CharField(max_length=80)
    required_role_ref = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="workflow_steps",
    )
    minimum_approvals = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["workflow_id", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["workflow", "sequence"], name="uniq_workflow_step_sequence"
            ),
            models.CheckConstraint(
                condition=Q(minimum_approvals__gte=1), name="workflow_step_approvals_positive"
            ),
        ]

    def clean(self):
        if self.required_role_ref_id and self.required_role_ref.organization_id != self.workflow.organization_id:
            raise ValidationError("Workflow step role must belong to the workflow organization.")

class ApprovalRequest(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="approval_requests"
    )
    workflow = models.ForeignKey(
        WorkflowDefinition, on_delete=models.PROTECT, related_name="approval_requests"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("content_type", "object_id")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_approval_requests",
    )
    current_step = models.ForeignKey(
        WorkflowStep,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="current_approval_requests",
    )
    status = models.CharField(
        max_length=16, choices=ApprovalStatus.choices, default=ApprovalStatus.DRAFT
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decided_approval_requests",
    )
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def clean(self):
        if self.workflow.organization_id != self.organization_id:
            raise ValidationError("Workflow must belong to the approval organization.")
        if self.current_step_id and self.current_step.workflow_id != self.workflow_id:
            raise ValidationError("Current approval step must belong to the request workflow.")
        if self.status == ApprovalStatus.APPROVED and not self.decided_at:
            raise ValidationError("Approved requests require decided_at.")

class ApprovalAction(TimeStampedModel):
    request = models.ForeignKey(
        ApprovalRequest, on_delete=models.CASCADE, related_name="actions"
    )
    step = models.ForeignKey(
        WorkflowStep,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="approval_actions",
    )
    action = models.CharField(max_length=16, choices=ApprovalActionType.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approval_actions"
    )
    comments = models.TextField(blank=True)
    acted_at = models.DateTimeField(default=timezone.now)

    def clean(self):
        if self.step_id and self.step.workflow_id != self.request.workflow_id:
            raise ValidationError("Approval action step must belong to the request workflow.")

class PlanningSubmission(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="planning_submissions"
    )
    workflow = models.ForeignKey(
        WorkflowDefinition, on_delete=models.PROTECT, related_name="planning_submissions"
    )
    scenario_version = models.ForeignKey(
        ScenarioVersion, on_delete=models.PROTECT, related_name="planning_submissions"
    )
    legal_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_submissions",
    )
    branch = models.ForeignKey(
        Branch,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_submissions",
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_submissions",
    )
    current_step = models.ForeignKey(
        WorkflowStep,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_submissions",
    )
    approval_request = models.OneToOneField(
        ApprovalRequest,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="planning_submission",
    )
    status = models.CharField(
        max_length=16, choices=SubmissionStatus.choices, default=SubmissionStatus.DRAFT
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="planning_submissions",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decided_planning_submissions",
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "scenario_version",
                    "legal_entity",
                    "branch",
                    "department",
                ],
                nulls_distinct=False,
                name="uniq_planning_submission_scope",
            ),
        ]

    def clean(self):
        if self.workflow.organization_id != self.organization_id:
            raise ValidationError("Submission workflow must belong to the organization.")
        if self.scenario_version.scenario.organization_id != self.organization_id:
            raise ValidationError("Submission scenario must belong to the organization.")
        if self.legal_entity_id and self.legal_entity.organization_id != self.organization_id:
            raise ValidationError("Submission entity must belong to the organization.")
        if self.branch_id:
            if self.branch.legal_entity.organization_id != self.organization_id:
                raise ValidationError("Submission branch must belong to the organization.")
            if self.legal_entity_id and self.branch.legal_entity_id not in (
                None,
                self.legal_entity_id,
            ):
                raise ValidationError("Submission branch must belong to the entity.")
        if self.department_id:
            department_entity_id = self.department.legal_entity_id or (
                self.department.branch.legal_entity_id
                if self.department.branch_id
                else None
            )
            if department_entity_id and self.legal_entity_id not in (
                None,
                department_entity_id,
            ):
                raise ValidationError("Submission department must belong to the entity.")
            if self.department.branch_id and self.branch_id:
                if self.department.branch_id != self.branch_id:
                    raise ValidationError("Submission department must belong to the branch.")
        if self.current_step_id and self.current_step.workflow_id != self.workflow_id:
            raise ValidationError("Submission current step must belong to its workflow.")
        if self.approval_request_id:
            if self.approval_request.organization_id != self.organization_id:
                raise ValidationError("Submission approval request must share its organization.")
            if self.approval_request.workflow_id != self.workflow_id:
                raise ValidationError("Submission approval request must use its workflow.")
        if self.status == SubmissionStatus.APPROVED and not self.decided_at:
            raise ValidationError("Approved submissions require decided_at.")

__all__ = ['Encumbrance', 'WorkflowDefinition', 'WorkflowStep', 'ApprovalRequest', 'ApprovalAction', 'PlanningSubmission']
