"""Tool protocol, decorator, and deterministic reference tool implementations."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, cast

from .context import ToolRequest
from .descriptor import ToolDescriptor
from .errors import ToolExecutionError, ToolValidationError
from .parameter import ToolParameter
from .result import ToolResult, ToolStatus
from .schema import ToolSchema


class Tool(Protocol):
    """Synchronous Tool contract with reserved async execution surface."""

    @property
    def descriptor(self) -> ToolDescriptor: ...

    def execute(self, request: ToolRequest) -> ToolResult: ...

    async def aexecute(self, request: ToolRequest) -> ToolResult: ...


@dataclass(frozen=True, slots=True)
class FunctionTool:
    """Reference wrapper for one local callable and a derived Tool descriptor."""

    function: Callable[..., object]
    descriptor: ToolDescriptor

    def execute(self, request: ToolRequest) -> ToolResult:
        """Validate and invoke the local callable without any remote tool transport."""
        if request.context.cancellation.is_set():
            return ToolResult(ToolStatus.CANCELLED)
        if (
            request.context.timeout_seconds is not None
            and request.context.timeout_seconds <= 0
        ):
            return ToolResult(ToolStatus.TIMED_OUT)
        if request.name != self.descriptor.name:
            raise ToolExecutionError(
                f"Tool request does not target {self.descriptor.name}."
            )
        arguments = self.descriptor.schema.validate(request.arguments)
        try:
            return ToolResult(ToolStatus.SUCCESS, self.function(**arguments))
        except Exception as error:
            return ToolResult(ToolStatus.ERROR, error=str(error))

    async def aexecute(self, request: ToolRequest) -> ToolResult:
        """Reserved async interface that delegates to the synchronous reference call."""
        return self.execute(request)


class EchoTool(FunctionTool):
    """Reference tool returning its explicit ``value`` argument unchanged."""

    def __init__(self, name: str = "echo") -> None:
        super().__init__(
            lambda value: value,
            ToolDescriptor(name, schema=ToolSchema((ToolParameter("value"),))),
        )


class MathTool(FunctionTool):
    """Reference arithmetic tool restricted to four deterministic local operations."""

    def __init__(self, name: str = "math") -> None:
        super().__init__(self._calculate, ToolDescriptor(name, schema=self._schema()))

    @staticmethod
    def _schema() -> ToolSchema:
        return ToolSchema(
            (
                ToolParameter("operation"),
                ToolParameter("left"),
                ToolParameter("right"),
            )
        )

    @staticmethod
    def _calculate(operation: object, left: object, right: object) -> object:
        if (
            not isinstance(operation, str)
            or not isinstance(left, (int, float))
            or not isinstance(right, (int, float))
        ):
            raise ToolExecutionError(
                "Math tool requires a string operation and numeric operands."
            )
        operations: dict[str, Callable[[float, float], float]] = {
            "add": lambda first, second: first + second,
            "subtract": lambda first, second: first - second,
            "multiply": lambda first, second: first * second,
            "divide": lambda first, second: first / second,
        }
        try:
            return operations[operation](left, right)
        except KeyError as error:
            raise ToolExecutionError(
                f"Unsupported math operation: {operation}"
            ) from error


class MemoryTool(FunctionTool):
    """Reference tool requiring an explicit compatible memory object in context."""

    def __init__(self, name: str = "memory") -> None:
        super().__init__(
            self._unconfigured,
            ToolDescriptor(name, schema=ToolSchema((ToolParameter("key"),))),
        )

    @staticmethod
    def _unconfigured(key: object) -> object:
        del key
        raise ToolExecutionError(
            "MemoryTool requires explicit context-aware execution."
        )

    def execute(self, request: ToolRequest) -> ToolResult:
        """Read one local record via the explicit context memory dependency."""
        if request.context.cancellation.is_set():
            return ToolResult(ToolStatus.CANCELLED)
        if (
            request.context.timeout_seconds is not None
            and request.context.timeout_seconds <= 0
        ):
            return ToolResult(ToolStatus.TIMED_OUT)
        arguments = self.descriptor.schema.validate(request.arguments)
        memory = request.context.memory
        if memory is None:
            return ToolResult(
                ToolStatus.ERROR, error="MemoryTool requires explicit memory."
            )
        get = getattr(memory, "get", None)
        if not callable(get):
            return ToolResult(
                ToolStatus.ERROR, error="MemoryTool requires compatible memory."
            )
        record = get(cast(str, arguments["key"]))
        return ToolResult(
            ToolStatus.SUCCESS, record.value if record is not None else None
        )


def _schema_for(function: Callable[..., object]) -> ToolSchema:
    parameters: list[ToolParameter] = []
    for parameter in inspect.signature(function).parameters.values():
        if parameter.kind not in {
            parameter.POSITIONAL_OR_KEYWORD,
            parameter.KEYWORD_ONLY,
        }:
            raise ToolValidationError("Reference tools require named parameters only.")
        required = parameter.default is inspect.Parameter.empty
        annotation = (
            "object"
            if parameter.annotation is inspect.Parameter.empty
            else str(parameter.annotation)
        )
        parameters.append(
            ToolParameter(
                parameter.name,
                annotation,
                required,
                None if required else parameter.default,
            )
        )
    return ToolSchema(tuple(parameters))


def tool(
    target: Callable[..., object] | None = None,
    *,
    name: str | None = None,
    description: str = "",
    registry: ToolRegistry | None = None,
) -> FunctionTool | Callable[[Callable[..., object]], FunctionTool]:
    """Decorate and register a local callable in an explicit or default SDK registry."""

    def decorate(function: Callable[..., object]) -> FunctionTool:
        selected_name = name or function.__name__
        created = FunctionTool(
            function,
            ToolDescriptor(selected_name, description, _schema_for(function)),
        )
        selected_registry = registry
        if selected_registry is None:
            from .registry import default_registry

            selected_registry = default_registry
        selected_registry.register(created)
        return created

    return decorate if target is None else decorate(target)


if TYPE_CHECKING:
    from .registry import ToolRegistry
