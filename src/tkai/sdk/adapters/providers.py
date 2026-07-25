"""Explicit provider adaptation and deterministic offline reference provider."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol, cast

from ..agent import AgentRequest, AgentResponse
from ..errors import AdapterError, InvalidRequestError, ProviderExecutionError
from ..providers import Provider, ProviderCapability, ProviderDescriptor


class CallableProvider(Protocol):
    """Optional extension supported by providers that expose named SDK calls."""

    def call(self, name: str, request: AgentRequest) -> AgentResponse: ...


class ProviderAdapter:
    """Adapt an injected Provider without owning its lifecycle or configuration."""

    def __init__(self, provider: Provider) -> None:
        self.provider = provider

    def chat(self, request: AgentRequest) -> AgentResponse:
        """Validate and forward one request while preserving provider failures."""
        self._validate(request)
        try:
            return self.provider.chat(request)
        except Exception as error:
            raise ProviderExecutionError("Provider chat execution failed.") from error

    def stream(self, request: AgentRequest) -> Iterable[AgentResponse]:
        """Yield the upstream iterable directly and wrap only raised provider errors."""
        self._validate(request)
        try:
            upstream = self.provider.stream(request)
        except Exception as error:
            raise ProviderExecutionError("Provider stream creation failed.") from error

        def responses() -> Iterable[AgentResponse]:
            try:
                yield from upstream
            except Exception as error:
                raise ProviderExecutionError(
                    "Provider stream execution failed."
                ) from error

        return responses()

    def call(self, name: str, request: AgentRequest) -> AgentResponse:
        """Delegate a named call when the injected provider explicitly supports it."""
        self._validate(request)
        if not hasattr(self.provider, "call"):
            raise AdapterError("Injected provider does not support named SDK calls.")
        try:
            return cast(CallableProvider, self.provider).call(name, request)
        except Exception as error:
            raise ProviderExecutionError("Provider call execution failed.") from error

    @staticmethod
    def _validate(request: AgentRequest) -> None:
        if request.input is None:
            raise InvalidRequestError("Agent request input must not be None.")


class InMemoryProvider:
    """Deterministic reference/testing provider; never accesses network or secrets."""

    def __init__(
        self,
        name: str = "in-memory",
        responder: Callable[[AgentRequest], object] | None = None,
    ) -> None:
        self._descriptor = ProviderDescriptor(
            name,
            frozenset(
                {
                    ProviderCapability.CHAT,
                    ProviderCapability.STREAMING,
                    ProviderCapability.TOOLS,
                }
            ),
        )
        self._responder = responder or (lambda request: request.input)
        self.closed = False

    @property
    def descriptor(self) -> ProviderDescriptor:
        """Return immutable reference-provider capability metadata."""
        return self._descriptor

    def chat(self, request: AgentRequest) -> AgentResponse:
        """Return deterministic local output from the injected responder."""
        return AgentResponse(
            self._responder(request), {"provider": self._descriptor.name}
        )

    def stream(self, request: AgentRequest) -> Iterable[AgentResponse]:
        """Yield exactly one local response without threads or unbounded buffering."""
        yield self.chat(request)

    def call(self, name: str, request: AgentRequest) -> AgentResponse:
        """Return deterministic local output annotated with the named capability."""
        response = self.chat(request)
        return AgentResponse(response.output, {**response.metadata, "call": name})

    def close(self) -> None:
        """Mark the reference provider closed; no external resource exists."""
        self.closed = True
