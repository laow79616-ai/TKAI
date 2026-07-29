"""Enterprise TikTok Business Workspace orchestration service."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from time import monotonic
from typing import Any

from .adapters import (
    AnalyticsPort,
    CoordinationPort,
    NullAnalyticsPort,
    NullCoordinationPort,
)
from .metrics import BusinessMetrics
from .models import (
    ApprovalStatus,
    BusinessApproval,
    BusinessOperation,
    BusinessProject,
    BusinessScope,
    BusinessWorkspace,
    CalendarEntry,
    CoordinationRequest,
    CoordinationTarget,
    LifecycleStatus,
    Member,
    Permission,
    Role,
    utcnow,
)

TRANSITIONS = {
    LifecycleStatus.DRAFT: {
        LifecycleStatus.PLANNING,
        LifecycleStatus.ARCHIVED,
        LifecycleStatus.DELETED,
    },
    LifecycleStatus.PLANNING: {
        LifecycleStatus.ACTIVE,
        LifecycleStatus.REVIEW,
        LifecycleStatus.ARCHIVED,
    },
    LifecycleStatus.ACTIVE: {
        LifecycleStatus.REVIEW,
        LifecycleStatus.PAUSED,
    },
    LifecycleStatus.REVIEW: {
        LifecycleStatus.APPROVED,
        LifecycleStatus.PLANNING,
    },
    LifecycleStatus.APPROVED: {
        LifecycleStatus.RUNNING,
        LifecycleStatus.PAUSED,
    },
    LifecycleStatus.RUNNING: {
        LifecycleStatus.PAUSED,
        LifecycleStatus.COMPLETED,
    },
    LifecycleStatus.PAUSED: {
        LifecycleStatus.PLANNING,
        LifecycleStatus.ACTIVE,
        LifecycleStatus.RUNNING,
        LifecycleStatus.ARCHIVED,
    },
    LifecycleStatus.COMPLETED: {LifecycleStatus.ARCHIVED},
    LifecycleStatus.ARCHIVED: {
        LifecycleStatus.DRAFT,
        LifecycleStatus.DELETED,
    },
    LifecycleStatus.DELETED: set(),
}

EXECUTION_TARGETS = {
    CoordinationTarget.PUBLISHING_CENTER,
    CoordinationTarget.AUTOMATION_ENGINE,
    CoordinationTarget.EXECUTION_ENGINE,
    CoordinationTarget.RUNTIME_MANAGER,
}


class TikTokBusinessWorkspace:
    """Tenant-isolated operational workspace with proposal-only coordination."""

    def __init__(
        self,
        *,
        coordinators: dict[CoordinationTarget, CoordinationPort] | None = None,
        analytics_center: AnalyticsPort | None = None,
    ) -> None:
        self.coordinators = coordinators or {}
        self.analytics_center = analytics_center or NullAnalyticsPort()
        self.workspaces: dict[str, BusinessWorkspace] = {}
        self.projects: dict[str, BusinessProject] = {}
        self.operations: dict[str, BusinessOperation] = {}
        self.calendar_entries: dict[str, CalendarEntry] = {}
        self.members: dict[str, Member] = {}
        self.roles: dict[str, Role] = {}
        self.approvals: dict[str, BusinessApproval] = {}
        self.coordination: dict[str, dict[str, str]] = {}
        self.audit: list[dict[str, str]] = []
        self.metrics = BusinessMetrics()

    @staticmethod
    def _require(scope: BusinessScope, action: str) -> None:
        permission = f"tiktok:business:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:business:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: BusinessScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    @staticmethod
    def _visible(values: Iterable[Any], scope: BusinessScope) -> list[Any]:
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def _audit(self, action: str, resource: str, scope: BusinessScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "actor": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "occurred_at": utcnow().isoformat(),
            }
        )

    def _measure(self, started: float) -> None:
        self.metrics.set("tiktok_business_latency_seconds", monotonic() - started)

    def create_workspace(
        self, item: BusinessWorkspace, scope: BusinessScope
    ) -> BusinessWorkspace:
        started = monotonic()
        self._require(scope, "write")
        self._scoped(item, scope)
        item.validate()
        if item.id in self.workspaces:
            raise ValueError("Workspace ID must be unique.")
        self.workspaces[item.id] = item
        self.metrics.increment("tiktok_business_workspaces_total")
        self._audit("workspace.create", item.id, scope)
        self._measure(started)
        return item

    def list_workspaces(self, scope: BusinessScope) -> list[BusinessWorkspace]:
        self._require(scope, "read")
        return [
            item
            for item in self._visible(self.workspaces.values(), scope)
            if item.status is not LifecycleStatus.DELETED
        ]

    def update_workspace(
        self, workspace_id: str, changes: dict[str, Any], scope: BusinessScope
    ) -> BusinessWorkspace:
        self._require(scope, "write")
        item = self.workspaces[workspace_id]
        self._scoped(item, scope)
        allowed = {"name", "description", "owner", "priority", "metadata"}
        if set(changes) - allowed:
            raise ValueError("Only bounded workspace fields may be updated.")
        for key, value in changes.items():
            setattr(item, key, value)
        item.version += 1
        item.updated_at = utcnow()
        item.validate()
        self._audit("workspace.update", item.id, scope)
        return item

    def delete_workspace(
        self, workspace_id: str, scope: BusinessScope
    ) -> BusinessWorkspace:
        self._require(scope, "delete")
        item = self.workspaces[workspace_id]
        self._scoped(item, scope)
        item.status = LifecycleStatus.DELETED
        item.version += 1
        item.updated_at = utcnow()
        self._audit("workspace.delete", item.id, scope)
        return item

    def create_project(
        self, item: BusinessProject, scope: BusinessScope
    ) -> BusinessProject:
        started = monotonic()
        self._require(scope, "write")
        self._scoped(item, scope)
        item.validate()
        self._scoped(self.workspaces[item.business_workspace_id], scope)
        if item.id in self.projects:
            raise ValueError("Project ID must be unique.")
        self.projects[item.id] = item
        self.metrics.increment("tiktok_business_projects_total")
        if item.campaign_reference:
            self.metrics.increment("tiktok_business_campaigns_total")
        self._audit("project.create", item.id, scope)
        self._measure(started)
        return item

    def create_operation(
        self, item: BusinessOperation, scope: BusinessScope
    ) -> BusinessOperation:
        self._require(scope, "write")
        self._scoped(item, scope)
        item.validate()
        self._scoped(self.projects[item.project_id], scope)
        if item.id in self.operations:
            raise ValueError("Operation ID must be unique.")
        self.operations[item.id] = item
        self.metrics.increment("tiktok_business_operations_total")
        self._audit("operation.create", item.id, scope)
        return item

    def add_calendar_entry(
        self, item: CalendarEntry, scope: BusinessScope
    ) -> CalendarEntry:
        self._require(scope, "schedule")
        self._scoped(item, scope)
        item.validate()
        self._scoped(self.projects[item.project_id], scope)
        self.calendar_entries[item.id] = item
        self._audit("calendar.create", item.id, scope)
        return item

    def add_role(self, item: Role, scope: BusinessScope) -> Role:
        self._require(scope, "manage_members")
        self._scoped(item, scope)
        item.validate()
        self.roles[item.id] = item
        self._audit("role.create", item.id, scope)
        return item

    def add_member(self, item: Member, scope: BusinessScope) -> Member:
        self._require(scope, "manage_members")
        self._scoped(item, scope)
        self._scoped(self.workspaces[item.business_workspace_id], scope)
        role = self.roles[item.role_id]
        self._scoped(role, scope)
        self.members[item.id] = item
        self._audit("member.add", item.id, scope)
        return item

    def authorize_member(
        self, member_id: str, permission: Permission, scope: BusinessScope
    ) -> bool:
        self._require(scope, "read")
        member = self.members[member_id]
        self._scoped(member, scope)
        role = self.roles[member.role_id]
        self._scoped(role, scope)
        return member.active and permission in role.permissions

    def decide_approval(
        self, item: BusinessApproval, scope: BusinessScope
    ) -> BusinessApproval:
        self._require(scope, "approve")
        self._scoped(item, scope)
        if item.status is ApprovalStatus.APPROVED and (
            item.expires_at is not None and item.expires_at <= utcnow()
        ):
            raise ValueError("Cannot approve with a past expiration.")
        if item.status is ApprovalStatus.REJECTED and not item.notes:
            raise ValueError("Rejected approvals require notes.")
        if item.status is not ApprovalStatus.PENDING:
            item.decided_at = utcnow()
        self.approvals[item.id] = item
        self.metrics.increment("tiktok_business_approvals_total")
        self._audit(f"approval.{item.status.value}", item.id, scope)
        return item

    def _has_approval(self, reference: str, scope: BusinessScope) -> bool:
        return any(
            (item.id == reference or item.resource_reference == reference)
            and item.active
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
            for item in self.approvals.values()
        )

    def transition(
        self, resource_id: str, target: LifecycleStatus, scope: BusinessScope
    ) -> BusinessWorkspace | BusinessProject | BusinessOperation:
        self._require(scope, "write")
        item = (
            self.projects.get(resource_id)
            or self.operations.get(resource_id)
            or self.workspaces[resource_id]
        )
        self._scoped(item, scope)
        if target not in TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid business lifecycle: {item.status.value} -> {target.value}"
            )
        if target in {LifecycleStatus.APPROVED, LifecycleStatus.RUNNING} and not (
            self._has_approval(f"ref://business/{resource_id}", scope)
        ):
            raise PermissionError("Current approval is required.")
        item.status = target
        if hasattr(item, "version"):
            item.version += 1
        if hasattr(item, "updated_at"):
            item.updated_at = utcnow()
        self._audit(f"lifecycle.{target.value}", resource_id, scope)
        return item

    def coordinate(self, request: CoordinationRequest, scope: BusinessScope) -> str:
        started = monotonic()
        self._require(scope, "coordinate")
        self._scoped(request, scope)
        request.validate()
        project = self.projects[request.project_id]
        self._scoped(project, scope)
        if request.target in EXECUTION_TARGETS:
            if not request.approval_reference or not self._has_approval(
                request.approval_reference, scope
            ):
                raise PermissionError(
                    "Execution and publishing proposals require current approval."
                )
        port = self.coordinators.get(request.target, NullCoordinationPort())
        receipt = port.coordinate(
            request.target.value,
            request.reference,
            scope.tenant,
            scope.workspace,
            scope.actor,
        )
        self.coordination[request.id] = {
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            "project_id": request.project_id,
            "target": request.target.value,
            "reference": request.reference,
            "receipt": receipt,
            "mode": "proposal_only",
        }
        self._audit("coordination.proposed", request.id, scope)
        self._measure(started)
        return receipt

    def analytics(self, scope: BusinessScope) -> dict[str, Any]:
        self._require(scope, "read")
        workspaces = self._visible(self.workspaces.values(), scope)
        projects = self._visible(self.projects.values(), scope)
        operations = self._visible(self.operations.values(), scope)
        campaigns = sum(bool(item.campaign_reference) for item in projects)
        external = {
            item.id: self.analytics_center.workspace_kpis(
                item.id, scope.tenant, scope.workspace
            )
            for item in workspaces
        }
        return {
            "workspace_kpis": {
                "total": len(workspaces),
                "active": sum(
                    item.status is LifecycleStatus.ACTIVE for item in workspaces
                ),
            },
            "project_kpis": {
                "total": len(projects),
                "completed": sum(
                    item.status is LifecycleStatus.COMPLETED for item in projects
                ),
            },
            "campaign_kpis": {"referenced": campaigns},
            "operational_kpis": {
                "total": len(operations),
                "running": sum(
                    item.status is LifecycleStatus.RUNNING for item in operations
                ),
            },
            "execution_kpis": {"proposals": len(self.coordination)},
            "resource_kpis": {
                "references": sum(len(item.resource_references) for item in operations)
            },
            "trend": external,
        }

    def history(self, scope: BusinessScope) -> dict[str, Any]:
        self._require(scope, "history")
        audit = [
            item
            for item in self.audit
            if item["tenant"] == scope.tenant and item["workspace"] == scope.workspace
        ]
        return {
            "workspace_history": [
                item.to_dict()
                for item in self._visible(self.workspaces.values(), scope)
            ],
            "project_history": [
                asdict(item) for item in self._visible(self.projects.values(), scope)
            ],
            "approval_history": [
                asdict(item) for item in self._visible(self.approvals.values(), scope)
            ],
            "coordination_history": [
                item
                for item in self.coordination.values()
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ],
            "analytics_history": self.analytics(scope),
            "audit_trail": audit,
        }

    def dashboard(self, scope: BusinessScope) -> dict[str, Any]:
        return {
            "sections": [
                "Workspace Overview",
                "Projects",
                "Operations",
                "Campaigns",
                "Calendar",
                "Members",
                "Approvals",
                "Analytics",
                "History",
            ],
            "overview": {
                "workspaces": len(self.list_workspaces(scope)),
                "projects": len(self._visible(self.projects.values(), scope)),
                "operations": len(self._visible(self.operations.values(), scope)),
                "members": len(self._visible(self.members.values(), scope)),
            },
            "analytics": self.analytics(scope),
            "safety": {
                "direct_publishing": False,
                "direct_execution": False,
                "approval_enforced": True,
                "proposal_only_coordination": True,
            },
        }
