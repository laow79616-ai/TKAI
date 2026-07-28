"""Application Center orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .catalog import ApplicationCatalog
from .deployment import DeploymentService
from .marketplace import ApplicationMarketplace
from .models import Application, ApplicationStatus, SharingScope
from .permissions import PermissionService
from .runtime import ApplicationMetrics, ApplicationRuntime, AuditEvent
from .templates import TemplateCatalog
from .versions import VersionStore

TRANSITIONS = {
    ApplicationStatus.DRAFT: {
        ApplicationStatus.PUBLISHED,
        ApplicationStatus.ARCHIVED,
        ApplicationStatus.DELETED,
    },
    ApplicationStatus.PUBLISHED: {
        ApplicationStatus.RUNNING,
        ApplicationStatus.ARCHIVED,
        ApplicationStatus.DELETED,
    },
    ApplicationStatus.RUNNING: {ApplicationStatus.PAUSED, ApplicationStatus.ARCHIVED},
    ApplicationStatus.PAUSED: {
        ApplicationStatus.RUNNING,
        ApplicationStatus.ARCHIVED,
        ApplicationStatus.DELETED,
    },
    ApplicationStatus.ARCHIVED: {ApplicationStatus.DRAFT, ApplicationStatus.DELETED},
    ApplicationStatus.DELETED: set(),
}


class ApplicationCenter:
    def __init__(self) -> None:
        self.catalog = ApplicationCatalog()
        self.templates = TemplateCatalog()
        self.metrics = ApplicationMetrics()
        self.runtime = ApplicationRuntime(self.metrics)
        self.deployments = DeploymentService(self.metrics)
        self.versions = VersionStore()
        self.permissions = PermissionService()
        self.marketplace = ApplicationMarketplace(self.catalog)

    def create(self, payload: dict[str, Any], actor: str | None = None) -> Application:
        item = self.catalog.create(payload)
        self.metrics.increment("applications_total")
        self.runtime.audit.append(
            AuditEvent("application.created", actor or item.owner, item.id, {})
        )
        return item

    def transition(self, application_id: str, status: str, actor: str) -> Application:
        item = self.catalog.get(application_id)
        target = ApplicationStatus(status)
        if target not in TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid transition: {item.status.value} -> {target.value}"
            )
        if target is ApplicationStatus.PUBLISHED:
            self.versions.create(item, actor)
        updated = self.catalog.replace(replace(item, status=target))
        self.runtime.audit.append(
            AuditEvent(
                f"application.{target.value}",
                actor,
                application_id,
                {"previous": item.status.value},
            )
        )
        return updated

    def share(self, application_id: str, scope: str, actor: str) -> Application:
        item = self.catalog.get(application_id)
        if item.owner != actor and not self.permissions.check(
            application_id, actor, "admin"
        ):
            raise PermissionError("Only the owner or an administrator may share.")
        return self.catalog.replace(replace(item, sharing=SharingScope(scope)))
