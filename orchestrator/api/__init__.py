"""FastAPI-compatible orchestrator API."""

from dataclasses import asdict
from typing import Any

from ..models import Scope
from ..service import EnterpriseAIOrchestrator


def register_orchestrator_routes(app: Any, service: EnterpriseAIOrchestrator) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["orchestrator"])

    def scope(tenant: str, actor: str) -> Scope:
        return Scope(tenant, actor)

    add(
        "/orchestrator",
        lambda tenant, actor: service.dashboard(scope(tenant, actor)),
        ["GET"],
    )
    add(
        "/plans",
        lambda tenant, actor: {
            "data": [p.to_dict() for p in service.list_plans(scope(tenant, actor))]
        },
        ["GET"],
    )
    add(
        "/plans",
        lambda payload: service.create_plan(
            dict(payload), scope(str(payload["tenant"]), str(payload["actor"]))
        ).to_dict(),
        ["POST"],
    )
    add(
        "/executions",
        lambda tenant, actor: {
            "data": [e.to_dict() for e in service.list_executions(scope(tenant, actor))]
        },
        ["GET"],
    )
    add(
        "/executions",
        lambda payload: service.submit(
            str(payload["plan_id"]),
            scope(str(payload["tenant"]), str(payload["actor"])),
            delay_seconds=float(payload.get("delay_seconds", 0)),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/executions/{execution_id}",
        lambda execution_id, tenant, actor: service.execute(
            execution_id, scope(tenant, actor)
        ).to_dict(),
        ["POST"],
    )
    add(
        "/queues",
        lambda: {
            "depth": service.queue.depth,
            "dead_letter": service.queue.dead_letters,
        },
        ["GET"],
    )
    add(
        "/checkpoints",
        lambda tenant: {"data": [asdict(c) for c in service.checkpoints.list(tenant)]},
        ["GET"],
    )
    add(
        "/recovery",
        lambda payload: service.resume(
            str(payload["execution_id"]),
            scope(str(payload["tenant"]), str(payload["actor"])),
            str(payload["checkpoint_id"]),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/recovery/rollback",
        lambda payload: service.rollback(
            str(payload["execution_id"]),
            scope(str(payload["tenant"]), str(payload["actor"])),
        ).to_dict(),
        ["POST"],
    )
