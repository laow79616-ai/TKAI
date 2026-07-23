"""Offline contract, reference-provider, factory, registry, and stream coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from tkai.sdk.provider import (
    MiddlewarePipeline,
    ProviderCapability,
    ProviderConfiguration,
    ProviderFactory,
    ProviderLifecycle,
    ProviderLifecycleError,
    ProviderRegistry,
    ProviderRequest,
    ReferenceProvider,
)
from tkai.sdk.provider.errors import ProviderNotFoundError


def test_reference_provider_capabilities_lifecycle_and_finite_stream() -> None:
    """Reference clients produce deterministic local responses and finish chunks."""
    provider = ReferenceProvider(responder=lambda request: f"echo:{request.input}")
    response = provider.execute(ProviderRequest("hello", model="local"))
    chunks = list(provider.stream(ProviderRequest("hello")))

    assert response.output == "echo:hello"
    assert ProviderCapability.CHAT in provider.capabilities
    assert chunks[0].response is not None
    assert chunks[-1].finished
    provider.close()
    assert provider.lifecycle is ProviderLifecycle.CLOSED
    with pytest.raises(ProviderLifecycleError):
        provider.execute(ProviderRequest("closed"))


def test_configuration_registry_factory_and_capability_lookup_are_explicit() -> None:
    """No provider is created until a caller registers and constructs it."""
    configuration = ProviderConfiguration(
        model="reference", headers={"x-local": "yes"}, metadata={"safe": True}
    )
    factory = ProviderFactory()
    factory.register(
        "reference", lambda config: ReferenceProvider(configuration=config)
    )
    provider = factory.create("reference", configuration)
    registry = ProviderRegistry()
    registry.register(provider)

    assert registry.lookup("reference") is provider
    assert registry.supports("reference", ProviderCapability.STREAMING)
    assert registry.unregister("reference") is provider
    with pytest.raises(ProviderNotFoundError):
        registry.lookup("reference")


def test_stream_cancel_close_and_middleware_error_path_are_local() -> None:
    """Streaming cleanup and error hooks do not start background or network work."""
    stream = ReferenceProvider().stream(ProviderRequest("one"))
    assert next(stream).response is not None
    stream.cancel()
    assert stream.cancelled and stream.closed

    events: list[str] = []

    class Middleware:
        def before_request(self, request: ProviderRequest) -> ProviderRequest:
            events.append("before")
            return request

        def after_response(self, response):
            events.append("after")
            return response

        def on_error(self, error: Exception) -> None:
            del error
            events.append("error")

    pipeline = MiddlewarePipeline((Middleware(),))
    assert (
        pipeline.execute(ProviderRequest("ok"), ReferenceProvider().execute).output
        == "ok"
    )
    with pytest.raises(RuntimeError):
        pipeline.execute(
            ProviderRequest("bad"),
            lambda _request: (_ for _ in ()).throw(RuntimeError("offline")),
        )
    assert events == ["before", "after", "before", "error"]


def test_registry_thread_safety_keeps_stable_local_client_set() -> None:
    """Concurrent registration is serialized without implicit provider ownership."""
    registry = ProviderRegistry()
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda index: registry.register(ReferenceProvider(f"p{index}")),
                range(32),
            )
        )
    assert [provider.name for provider in registry.list()] == sorted(
        f"p{index}" for index in range(32)
    )
