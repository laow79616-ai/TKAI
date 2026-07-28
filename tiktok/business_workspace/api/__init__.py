"""HTTP registration for the Enterprise TikTok Business Workspace."""

from __future__ import annotations

from typing import Any

from ..models import (
    BusinessApproval,
    BusinessOperation,
    BusinessProject,
    BusinessScope,
    BusinessWorkspace,
    CalendarEntry,
    CoordinationRequest,
    LifecycleStatus,
    Member,
    Role,
)
from ..service import TikTokBusinessWorkspace

ROUTES = (
    "/tiktok/business-workspace/workspaces",
    "/tiktok/business-workspace/projects",
    "/tiktok/business-workspace/operations",
    "/tiktok/business-workspace/calendar",
    "/tiktok/business-workspace/members",
    "/tiktok/business-workspace/approvals",
    "/tiktok/business-workspace/analytics",
)
TAG = ["tiktok-business-workspace"]


def _scope() -> BusinessScope:
    return BusinessScope(
        "default", "default", "api", frozenset({"tiktok:business:admin"})
    )


def register_business_workspace_routes(
    app: Any, service: TikTokBusinessWorkspace
) -> None:
    def create_workspace(item: BusinessWorkspace) -> BusinessWorkspace:
        return service.create_workspace(item, _scope())

    def update_workspace(
        workspace_id: str, changes: dict[str, Any]
    ) -> BusinessWorkspace:
        return service.update_workspace(workspace_id, changes, _scope())

    def create_project(item: BusinessProject) -> BusinessProject:
        return service.create_project(item, _scope())

    def create_operation(item: BusinessOperation) -> BusinessOperation:
        return service.create_operation(item, _scope())

    def create_calendar_entry(item: CalendarEntry) -> CalendarEntry:
        return service.add_calendar_entry(item, _scope())

    def create_member(item: Member) -> Member:
        return service.add_member(item, _scope())

    def create_role(item: Role) -> Role:
        return service.add_role(item, _scope())

    def decide_approval(item: BusinessApproval) -> BusinessApproval:
        return service.decide_approval(item, _scope())

    def coordinate(item: CoordinationRequest) -> str:
        return service.coordinate(item, _scope())

    def transition(resource_id: str, target: LifecycleStatus) -> Any:
        return service.transition(resource_id, target, _scope())

    app.add_api_route(
        ROUTES[0], lambda: service.list_workspaces(_scope()), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        ROUTES[0],
        create_workspace,
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        f"{ROUTES[0]}/{{workspace_id}}",
        update_workspace,
        methods=["PATCH"],
        tags=TAG,
    )
    app.add_api_route(
        f"{ROUTES[0]}/{{workspace_id}}",
        lambda workspace_id: service.delete_workspace(workspace_id, _scope()),
        methods=["DELETE"],
        tags=TAG,
    )
    _register_collection(
        app,
        ROUTES[1],
        service.projects,
        create_project,
    )
    _register_collection(
        app,
        ROUTES[2],
        service.operations,
        create_operation,
    )
    _register_collection(
        app,
        ROUTES[3],
        service.calendar_entries,
        create_calendar_entry,
    )
    _register_collection(
        app,
        ROUTES[4],
        service.members,
        create_member,
    )
    _register_collection(
        app,
        ROUTES[5],
        service.approvals,
        decide_approval,
    )
    app.add_api_route(
        "/tiktok/business-workspace/roles",
        lambda: _scoped_values(service.roles, _scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/business-workspace/roles",
        create_role,
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/business-workspace/coordination",
        coordinate,
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[6], lambda: service.analytics(_scope()), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        "/tiktok/business-workspace/history",
        lambda: service.history(_scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/business-workspace/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/business-workspace/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/business-workspace/{resource_id}/transition",
        transition,
        methods=["POST"],
        tags=TAG,
    )


def _register_collection(
    app: Any, path: str, collection: dict[str, Any], creator: Any
) -> None:
    app.add_api_route(
        path,
        lambda: _scoped_values(collection, _scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(path, creator, methods=["POST"], tags=TAG)


def _scoped_values(
    collection: dict[str, Any], scope: BusinessScope
) -> list[Any]:
    return [
        item
        for item in collection.values()
        if item.tenant == scope.tenant and item.workspace == scope.workspace
    ]


# Keep these imports visible to FastAPI's annotation resolver.
API_MODELS = (
    BusinessWorkspace,
    BusinessProject,
    BusinessOperation,
    CalendarEntry,
    Member,
    Role,
    BusinessApproval,
    CoordinationRequest,
    LifecycleStatus,
)
