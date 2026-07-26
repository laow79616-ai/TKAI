"""Enterprise Agent Runtime HTTP adapters."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from tkai.agent import AgentApi


def create_endpoint(api: AgentApi) -> Callable[[Mapping[str, Any]], dict[str, Any]]:
    return api.create_agent


def list_endpoint(api: AgentApi) -> Callable[[], dict[str, Any]]:
    return api.list_agents


def run_endpoint(api: AgentApi) -> Callable[[Mapping[str, Any]], dict[str, Any]]:
    return api.run_agent


def get_run_endpoint(api: AgentApi) -> Callable[[str], dict[str, Any]]:
    return api.get_run


def delete_run_endpoint(api: AgentApi) -> Callable[[str], dict[str, bool]]:
    return api.delete_run

