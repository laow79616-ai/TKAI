"""Reference-only tool, decorator, registry, and middleware coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from tkai.sdk.memory import MemoryRecord, ReferenceMemory
from tkai.sdk.tools import (
    EchoTool,
    MathTool,
    MemoryTool,
    ToolContext,
    ToolFactory,
    ToolMiddlewarePipeline,
    ToolRegistry,
    ToolRequest,
    ToolStatus,
    ToolValidationError,
    tool,
)


def test_reference_tool_execution_validation_cancellation_and_timeout() -> None:
    """Reference tools validate local arguments without external execution paths."""
    echo = EchoTool()
    assert echo.execute(ToolRequest("echo", {"value": "local"})).output == "local"
    assert (
        echo.execute(
            ToolRequest("echo", {"value": "local"}, ToolContext(timeout_seconds=0))
        ).status
        is ToolStatus.TIMED_OUT
    )
    cancelled = ToolContext()
    cancelled.cancellation.set()
    assert (
        echo.execute(ToolRequest("echo", {"value": "unused"}, cancelled)).status
        is ToolStatus.CANCELLED
    )
    with pytest.raises(ToolValidationError):
        echo.execute(ToolRequest("echo", {}))


def test_decorator_registry_factory_and_math_reference_tool_are_explicit() -> None:
    """Decorated callables derive schemas and register only in the supplied registry."""
    registry = ToolRegistry()

    @tool(name="greeting", registry=registry)
    def greeting(person: str, punctuation: str = "!") -> str:
        return f"hello {person}{punctuation}"

    result = registry.lookup("greeting").execute(
        ToolRequest("greeting", {"person": "Ada"})
    )
    assert result.output == "hello Ada!"
    assert greeting.descriptor.schema.parameters[1].required is False

    factory = ToolFactory()
    factory.register("math", MathTool)
    math = factory.create("math")
    assert (
        math.execute(
            ToolRequest("math", {"operation": "multiply", "left": 6, "right": 7})
        ).output
        == 42
    )


def test_memory_tool_and_middleware_hooks_remain_local_and_isolated() -> None:
    """Memory and middleware integrations use explicitly supplied in-process state."""
    memory = ReferenceMemory()
    memory.store(MemoryRecord("note", "remembered"))
    assert (
        MemoryTool()
        .execute(ToolRequest("memory", {"key": "note"}, ToolContext(memory=memory)))
        .output
        == "remembered"
    )

    events: list[str] = []

    class Middleware:
        def before_execute(self, request: ToolRequest) -> ToolRequest:
            events.append("before")
            return request

        def after_execute(self, result):
            events.append("after")
            return result

        def on_error(self, error: Exception) -> None:
            del error
            events.append("error")

    pipeline = ToolMiddlewarePipeline((Middleware(),))
    assert (
        pipeline.execute(EchoTool(), ToolRequest("echo", {"value": "ok"})).output
        == "ok"
    )
    assert events == ["before", "after"]


def test_registry_thread_safety_has_stable_local_snapshots() -> None:
    """Concurrent registration has deterministic snapshots and no implicit transport."""
    registry = ToolRegistry()
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda index: registry.register(EchoTool(f"echo-{index}")), range(32)
            )
        )
    assert [item.descriptor.name for item in registry.list()] == sorted(
        f"echo-{index}" for index in range(32)
    )
