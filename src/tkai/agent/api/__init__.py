"""Transport-neutral Agent Runtime API adapters."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..definition import AgentDefinition
from ..models import AgentLimits
from ..runtime import AgentRuntime


class AgentApi:
    def __init__(self, runtime: AgentRuntime) -> None:
        self.runtime = runtime

    def create_agent(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        limits = payload.get("limits", {})
        if not isinstance(limits, Mapping):
            raise ValueError("Agent limits must be an object.")
        definition = AgentDefinition(
            agent_id=str(payload["agent_id"]),
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            version=str(payload["version"]),
            prompt=str(payload["prompt"]),
            tools=tuple(map(str, payload.get("tools", ()))),
            memory=tuple(map(str, payload.get("memory", ()))),
            permissions=tuple(map(str, payload.get("permissions", ()))),
            limits=AgentLimits(
                max_steps=int(limits.get("max_steps", 100)),
                timeout_seconds=float(limits.get("timeout_seconds", 300.0)),
                max_tool_calls=int(limits.get("max_tool_calls", 50)),
            ),
            metadata=dict(payload.get("metadata", {})),
        )
        return self.runtime.create(definition).to_dict()

    def list_agents(self) -> dict[str, Any]:
        records = [item.to_dict() for item in self.runtime.list_agents()]
        return {"data": records, "total": len(records), "error": None}

    def run_agent(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        agent_id = str(payload["agent_id"])
        agent = self.runtime.get_agent(agent_id)
        if agent.status.value == "draft":
            self.runtime.prepare(agent_id)
        return self.runtime.start_run(
            agent_id,
            str(payload["workspace"]),
            dict(payload.get("inputs", {})),
        ).to_dict()

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self.runtime.get_run(run_id).to_dict()

    def delete_run(self, run_id: str) -> dict[str, bool]:
        self.runtime.delete_run(run_id)
        return {"deleted": True}

