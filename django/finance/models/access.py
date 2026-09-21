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


class Role(TimeStampedModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="roles"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=120)
    permissions = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["organization_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_role_code_org"
            ),
        ]

class UserProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="finance_profile",
    )
    default_organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="default_user_profiles",
    )
    display_name = models.CharField(max_length=160, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.default_organization_id and self.default_organization.status != LifecycleStatus.ACTIVE:
            raise ValidationError("User profile default organization must be active.")

class UserOrgScope(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="finance_scopes"
    )
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="user_scopes")
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="user_scopes"
    )
    legal_entity = models.ForeignKey(
        LegalEntity,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="user_scopes",
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.CASCADE, related_name="user_scopes"
    )
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="user_scopes",
    )
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["user_id", "organization_id", "valid_from"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "role",
                    "organization",
                    "legal_entity",
                    "branch",
                    "department",
                    "valid_from",
                ],
                nulls_distinct=False,
                name="uniq_user_org_scope",
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=F("valid_from")),
                name="user_org_scope_valid_dates",
            ),
        ]

    def clean(self):
        if self.role_id and self.role.organization_id != self.organization_id:
            raise ValidationError("Role and user scope must share an organization.")
        if self.legal_entity_id and self.legal_entity.organization_id != self.organization_id:
            raise ValidationError("User scope entity must belong to the organization.")
        if self.branch_id:
            if self.branch.legal_entity_id and self.legal_entity_id not in (
                None,
                self.branch.legal_entity_id,
            ):
                raise ValidationError("User scope branch must belong to its entity.")
            if self.branch.legal_entity.organization_id != self.organization_id:
                raise ValidationError("User scope branch must belong to the organization.")
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
                raise ValidationError("User scope department must belong to its entity.")
            if self.department.branch_id and self.branch_id:
                if self.department.branch_id != self.branch_id:
                    raise ValidationError("User scope department must belong to its branch.")

__all__ = ['Role', 'UserProfile', 'UserOrgScope']
