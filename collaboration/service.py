"""Enterprise AI Collaboration Platform facade."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, TypeVar
from uuid import uuid4

from .metrics import CollaborationMetrics
from .models import (
    CollaborationScope,
    CollaborationSession,
    CollaborationTask,
    Handoff,
    HandoffType,
    Message,
    Notification,
    PresenceStatus,
    Project,
    ProjectStatus,
    SessionStatus,
    SharedContext,
    TaskPriority,
    TaskStatus,
    TimelineEvent,
    Workspace,
    WorkspaceStatus,
)
from .security import CollaborationSecurity

T = TypeVar("T")


class EnterpriseAICollaborationPlatform:
    """Coordinate scoped collaboration resources for humans, agents, and workflows."""

    def __init__(self) -> None:
        self.security = CollaborationSecurity()
        self.metrics = CollaborationMetrics()
        self.workspaces: dict[str, Workspace] = {}
        self.projects: dict[str, Project] = {}
        self.sessions: dict[str, CollaborationSession] = {}
        self.messages: dict[str, Message] = {}
        self.tasks: dict[str, CollaborationTask] = {}
        self.handoffs: dict[str, Handoff] = {}
        self.notifications: dict[str, Notification] = {}
        self.timeline: list[TimelineEvent] = []
        self.presence: dict[tuple[str, str, str], PresenceStatus] = {}
        self.shared_memory: dict[tuple[str, str, str], dict[str, Any]] = {}

    def create_workspace(
        self, payload: dict[str, Any], scope: CollaborationScope
    ) -> Workspace:
        self.security.require(scope, "collaboration:admin")
        identifier = str(payload.get("id") or scope.workspace)
        if identifier != scope.workspace:
            raise PermissionError("Workspace scope must match the workspace ID.")
        if identifier in self.workspaces:
            raise ValueError("Workspace already exists.")
        item = Workspace(
            id=identifier,
            tenant=scope.tenant,
            organization=str(payload["organization"]),
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            members=tuple(str(value) for value in payload.get("members", ())),
            roles={str(k): str(v) for k, v in payload.get("roles", {}).items()},
            status=WorkspaceStatus(str(payload.get("status", "active"))),
            metadata=dict(payload.get("metadata", {})),
        )
        self.workspaces[item.id] = item
        self.metrics.increment("workspaces_total")
        self._event(scope, "workspace", "created", item.id)
        return item

    def create_project(
        self, payload: dict[str, Any], scope: CollaborationScope
    ) -> Project:
        self.security.require(scope, "collaboration:write")
        self._workspace(scope)
        item = Project(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            owner=str(payload.get("owner", scope.actor)),
            applications=self._strings(payload.get("applications", ())),
            agents=self._strings(payload.get("agents", ())),
            knowledge=self._strings(payload.get("knowledge", ())),
            workflow=self._optional(payload.get("workflow")),
            status=ProjectStatus(str(payload.get("status", "draft"))),
            version=str(payload.get("version", "1.0.0")),
        )
        self._unique(self.projects, item.id, "Project")
        self.projects[item.id] = item
        self.metrics.increment("projects_total")
        self._event(scope, "project", "created", item.id)
        return item

    def create_session(
        self, payload: dict[str, Any], scope: CollaborationScope
    ) -> CollaborationSession:
        self.security.require(scope, "collaboration:write")
        self._workspace(scope)
        context = dict(payload.get("shared_context", {}))
        item = CollaborationSession(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            participants=self._strings(payload.get("participants", ())),
            agent_participants=self._strings(payload.get("agent_participants", ())),
            shared_context=SharedContext(
                variables=dict(context.get("variables", {})),
                artifacts=tuple(dict(v) for v in context.get("artifacts", ())),
                knowledge_references=self._strings(
                    context.get("knowledge_references", ())
                ),
                application_state=dict(context.get("application_state", {})),
                workflow_state=dict(context.get("workflow_state", {})),
            ),
            shared_memory_namespace=str(
                payload.get("shared_memory_namespace", "default")
            ),
            status=SessionStatus(str(payload.get("status", "open"))),
        )
        self._unique(self.sessions, item.id, "Collaboration session")
        self.sessions[item.id] = item
        self.metrics.increment("collaboration_sessions_total")
        self._event(scope, "session", "created", item.id)
        return item

    def set_presence(
        self, participant: str, status: str, scope: CollaborationScope
    ) -> PresenceStatus:
        self.security.require(scope, "collaboration:write")
        value = PresenceStatus(status)
        self.presence[(scope.tenant, scope.workspace, participant)] = value
        self._event(scope, "presence", value.value, participant)
        return value

    def send_message(
        self, payload: dict[str, Any], scope: CollaborationScope
    ) -> Message:
        self.security.require(scope, "collaboration:message")
        session = self._get(self.sessions, str(payload["session_id"]), scope)
        item = Message(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            session_id=session.id,
            thread_id=str(payload.get("thread_id") or uuid4()),
            sender=scope.actor,
            body=str(payload["body"]),
            mentions=self._strings(payload.get("mentions", ())),
            reply_to=self._optional(payload.get("reply_to")),
            attachments=tuple(dict(value) for value in payload.get("attachments", ())),
        )
        self.messages[item.id] = item
        self.metrics.increment("messages_total")
        self._event(scope, "message", "sent", item.id)
        for recipient in item.mentions:
            self.notify(recipient, "mention", f"{scope.actor} mentioned you", scope)
        return item

    def update_context(
        self, session_id: str, payload: dict[str, Any], scope: CollaborationScope
    ) -> SharedContext:
        self.security.require(scope, "collaboration:write")
        session = self._get(self.sessions, session_id, scope)
        current = session.shared_context
        updated = SharedContext(
            variables={**current.variables, **dict(payload.get("variables", {}))},
            artifacts=current.artifacts
            + tuple(dict(v) for v in payload.get("artifacts", ())),
            knowledge_references=tuple(
                dict.fromkeys(
                    current.knowledge_references
                    + self._strings(payload.get("knowledge_references", ()))
                )
            ),
            application_state={
                **current.application_state,
                **dict(payload.get("application_state", {})),
            },
            workflow_state={
                **current.workflow_state,
                **dict(payload.get("workflow_state", {})),
            },
        )
        session.shared_context = updated
        self._event(scope, "shared_context", "updated", session_id)
        return updated

    def write_memory(
        self,
        namespace: str,
        key: str,
        value: Any,
        scope: CollaborationScope,
    ) -> None:
        self.security.require(scope, "collaboration:memory:write")
        bucket = self.shared_memory.setdefault(
            (scope.tenant, scope.workspace, namespace), {}
        )
        bucket[key] = value
        self._event(scope, "shared_memory", "written", f"{namespace}:{key}")

    def read_memory(self, namespace: str, key: str, scope: CollaborationScope) -> Any:
        self.security.require(scope, "collaboration:memory:read")
        return self.shared_memory[(scope.tenant, scope.workspace, namespace)][key]

    def create_task(
        self, payload: dict[str, Any], scope: CollaborationScope
    ) -> CollaborationTask:
        self.security.require(scope, "collaboration:task")
        dependencies = self._strings(payload.get("dependencies", ()))
        missing = [value for value in dependencies if value not in self.tasks]
        if missing:
            raise ValueError(f"Unknown task dependencies: {', '.join(missing)}")
        item = CollaborationTask(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            title=str(payload["title"]),
            assignment=self._optional(payload.get("assignment")),
            priority=TaskPriority(str(payload.get("priority", "medium"))),
            status=TaskStatus(str(payload.get("status", "todo"))),
            due_date=self._optional(payload.get("due_date")),
            dependencies=dependencies,
            description=str(payload.get("description", "")),
        )
        self._unique(self.tasks, item.id, "Task")
        self.tasks[item.id] = item
        self.metrics.increment("tasks_total")
        self._event(scope, "task", "created", item.id)
        return item

    def update_task(
        self, task_id: str, payload: dict[str, Any], scope: CollaborationScope
    ) -> CollaborationTask:
        self.security.require(scope, "collaboration:task")
        item = self._get(self.tasks, task_id, scope)
        updated = replace(
            item,
            assignment=self._optional(payload.get("assignment", item.assignment)),
            priority=TaskPriority(str(payload.get("priority", item.priority.value))),
            status=TaskStatus(str(payload.get("status", item.status.value))),
            due_date=self._optional(payload.get("due_date", item.due_date)),
        )
        self.tasks[item.id] = updated
        self._event(scope, "task", "updated", item.id)
        return updated

    def handoff(self, payload: dict[str, Any], scope: CollaborationScope) -> Handoff:
        self.security.require(scope, "collaboration:handoff")
        item = Handoff(
            id=str(payload.get("id") or uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            source=str(payload["source"]),
            target=str(payload["target"]),
            type=HandoffType(str(payload["type"])),
            context=dict(payload.get("context", {})),
        )
        self.handoffs[item.id] = item
        self.metrics.increment("handoffs_total")
        self._event(scope, "handoff", item.type.value, item.id)
        self.notify(item.target, "handoff", f"Handoff from {item.source}", scope)
        return item

    def notify(
        self,
        recipient: str,
        type_: str,
        message: str,
        scope: CollaborationScope,
    ) -> Notification:
        item = Notification(
            id=str(uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            recipient=recipient,
            type=type_,
            message=message,
        )
        self.notifications[item.id] = item
        self.metrics.increment("notifications_total")
        return item

    def list_scoped(
        self, values: dict[str, T], scope: CollaborationScope, permission: str
    ) -> tuple[T, ...]:
        self.security.require(scope, permission)
        result = []
        for value in values.values():
            tenant = str(value.tenant)  # type: ignore[attr-defined]
            workspace = str(value.workspace)  # type: ignore[attr-defined]
            if tenant == scope.tenant and workspace == scope.workspace:
                result.append(value)
        return tuple(result)

    def dashboard(self, scope: CollaborationScope) -> dict[str, Any]:
        self.security.require(scope, "collaboration:read")
        return {
            "sections": (
                "Teams",
                "Projects",
                "Sessions",
                "Tasks",
                "Timeline",
                "Activity",
                "Notifications",
            ),
            "projects": len(
                self.list_scoped(self.projects, scope, "collaboration:read")
            ),
            "sessions": len(
                self.list_scoped(self.sessions, scope, "collaboration:read")
            ),
            "tasks": len(self.list_scoped(self.tasks, scope, "collaboration:read")),
            "timeline": [event.to_dict() for event in self.timeline_for(scope)],
            "notifications": [
                value.to_dict()
                for value in self.list_scoped(
                    self.notifications, scope, "collaboration:read"
                )
                if value.recipient == scope.actor
            ],
            "presence": {
                participant: status.value
                for (tenant, workspace, participant), status in self.presence.items()
                if tenant == scope.tenant and workspace == scope.workspace
            },
            "metrics": self.metrics.snapshot(),
        }

    def timeline_for(self, scope: CollaborationScope) -> tuple[TimelineEvent, ...]:
        self.security.require(scope, "collaboration:read")
        return tuple(
            event
            for event in self.timeline
            if event.tenant == scope.tenant and event.workspace == scope.workspace
        )

    def _workspace(self, scope: CollaborationScope) -> Workspace:
        item = self.workspaces[scope.workspace]
        self.security.isolate(scope, item.tenant, item.id)
        return item

    def _get(
        self, values: dict[str, T], identifier: str, scope: CollaborationScope
    ) -> T:
        item = values[identifier]
        self.security.isolate(
            scope,
            str(item.tenant),  # type: ignore[attr-defined]
            str(item.workspace),  # type: ignore[attr-defined]
        )
        return item

    def _event(
        self,
        scope: CollaborationScope,
        category: str,
        action: str,
        resource: str,
    ) -> None:
        event = TimelineEvent(
            id=str(uuid4()),
            tenant=scope.tenant,
            workspace=scope.workspace,
            actor=scope.actor,
            category=category,
            action=action,
            resource=resource,
        )
        self.timeline.append(event)
        self.security.record(
            scope, f"collaboration:{category}:{action}", resource=resource
        )

    @staticmethod
    def _unique(values: dict[str, Any], identifier: str, label: str) -> None:
        if identifier in values:
            raise ValueError(f"{label} already exists.")

    @staticmethod
    def _strings(values: Any) -> tuple[str, ...]:
        return tuple(str(value) for value in values)

    @staticmethod
    def _optional(value: Any) -> str | None:
        return None if value is None else str(value)
