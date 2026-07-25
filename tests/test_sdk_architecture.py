"""Tests for the additive TKAI 2.0 SDK architecture surface."""

from __future__ import annotations

import pytest

from tkai.sdk import (
    Agent,
    AgentRequest,
    AgentResponse,
    ConfigurationLoader,
    EnvironmentConfigurationSource,
    ExtensionKind,
    ExtensionRegistry,
    MappingConfigurationSource,
    Node,
    NodeKind,
    WorkflowBuilder,
)
from tkai.sdk.errors import SDKConfigurationError
from tkai.sdk.plugins import Extension


class _Runtime:
    def chat(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(request.input)

    def run(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(request.input)

    def stream(self, request: AgentRequest):
        return iter((AgentResponse(request.input),))

    def call(self, name: str, request: AgentRequest) -> AgentResponse:
        return AgentResponse(f"{name}:{request.input}")


def test_agent_delegates_to_explicit_runtime_without_provider_ownership() -> None:
    """The facade does not construct or modify a V1.x provider runtime."""
    agent = Agent(_Runtime())

    assert agent.chat("hello").output == "hello"
    assert agent.run("task").output == "task"
    assert [item.output for item in agent.stream("stream")] == ["stream"]
    assert agent.call("tool", "input").output == "tool:input"
    with pytest.raises(SDKConfigurationError):
        Agent().chat("unconfigured")


def test_workflow_builder_is_declarative_and_validates_graph_names() -> None:
    """Node kinds are stored without executing handlers or V1.x workflows."""
    definition = (
        WorkflowBuilder("sdk")
        .add(Node("start", NodeKind.CONDITION, successors=("parallel",)))
        .add(Node("parallel", NodeKind.PARALLEL))
        .build()
    )

    assert definition.entrypoint == "start"
    assert [node.kind for node in definition.nodes] == [
        NodeKind.CONDITION,
        NodeKind.PARALLEL,
    ]


def test_extension_registry_and_configuration_sources_are_local_and_additive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Extension metadata and configuration precedence remain SDK-local."""
    extensions = ExtensionRegistry()
    extensions.register(Extension("echo", ExtensionKind.TOOL, object()))
    assert [item.name for item in extensions.list()] == ["echo"]

    monkeypatch.setenv("TKAI_TIMEOUT", "30")
    configuration = ConfigurationLoader(
        (
            MappingConfigurationSource({"timeout": 5, "model": "local"}),
            EnvironmentConfigurationSource(),
        )
    ).load()
    assert configuration.get("timeout") == "30"
    assert configuration.get("model") == "local"
