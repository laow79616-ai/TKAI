"""FastAPI-compatible reasoning engine API."""

from __future__ import annotations

from typing import Any

from ..models import ReasoningScope
from ..service import EnterpriseAIReasoningEngine


def register_reasoning_routes(app: Any, service: EnterpriseAIReasoningEngine) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["reasoning"])

    def scope(payload: dict[str, Any]) -> ReasoningScope:
        return ReasoningScope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["actor"]),
        )

    add(
        "/reasoning",
        lambda tenant, workspace, actor: {
            "data": [
                item.to_dict()
                for item in service.list(ReasoningScope(tenant, workspace, actor))
            ]
        },
        ["GET"],
    )
    add(
        "/reasoning",
        lambda payload: service.create_session(dict(payload), scope(payload)).to_dict(),
        ["POST"],
    )
    add(
        "/reasoning/plans",
        lambda payload: service.create_plan(
            str(payload["session_id"]),
            list(payload.get("subtasks", ())),
            scope(payload),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/reasoning/decisions",
        lambda payload: service.decide(
            str(payload["session_id"]),
            list(payload.get("options", ())),
            scope(payload),
            threshold=payload.get("threshold", 0.5),
            fallback=payload.get("fallback"),
            rules=payload.get("rules", ()),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/reasoning/validation",
        lambda payload: service.validate(
            str(payload["session_id"]),
            dict(payload.get("constraints", {})),
            scope(payload),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/reasoning/simulation",
        lambda payload: {
            "data": [
                result.to_dict()
                for result in service.simulate(
                    str(payload["session_id"]),
                    list(payload.get("scenarios", ())),
                    scope(payload),
                )
            ]
        },
        ["POST"],
    )
