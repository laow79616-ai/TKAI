"""Validate only lifecycle APIs that exist in the current local implementation."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from tkai.ai.runtime import OwnershipPolicy, ProviderRuntime, RuntimeLifecycleError
from tkai.distributed import DistributedCoordinator, Node
from tkai.providers.http import AsyncHTTPTransport
from tkai.telemetry import TelemetryManager


class _Transport:
    def __init__(self) -> None:
        self.closed = False

    async def request(self, method: str, url: str, **kwargs: object) -> object:
        del method, url, kwargs
        return {}

    async def stream(self, method: str, url: str, **kwargs: object):
        del method, url, kwargs
        if False:
            yield b""

    async def close(self) -> None:
        self.closed = True

    def health_check(self) -> bool:
        return not self.closed


def _node() -> Node:
    now = datetime.now(timezone.utc)
    return Node("local", "localhost", now, now)


def test_telemetry_and_coordinator_lifecycle_calls_are_idempotent() -> None:
    """Repeat real start/stop operations without retaining a started local runtime."""
    telemetry = TelemetryManager()
    telemetry.start()
    telemetry.start()
    assert telemetry.registry.get("local").health()
    telemetry.stop()
    telemetry.stop()
    assert not telemetry.registry.get("local").health()

    coordinator = DistributedCoordinator(_node())
    coordinator.start()
    coordinator.start()
    assert coordinator.summary()["started"] is True
    coordinator.stop()
    coordinator.stop()
    assert coordinator.summary()["started"] is False
    assert coordinator.membership.snapshot() == []


def test_provider_runtime_and_async_transport_close_lifecycle_is_safe() -> None:
    """Close owned resources once, preserve external ownership, and reject re-use."""

    async def exercise() -> None:
        owned = _Transport()
        runtime = ProviderRuntime(owned, ownership=OwnershipPolicy.RUNTIME_OWNED)
        async with runtime.request_scope() as selected:
            assert selected is owned
        assert runtime.health()["lifecycle"] == "initialized"
        await runtime.close()
        await runtime.close()
        assert owned.closed
        with pytest.raises(RuntimeLifecycleError):
            await runtime.initialize()

        external = _Transport()
        external_runtime = ProviderRuntime(
            external, ownership=OwnershipPolicy.EXTERNALLY_OWNED
        )
        await external_runtime.close()
        assert not external.closed

        client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(200))
        )
        async with AsyncHTTPTransport(client) as http_transport:
            assert await http_transport.get("https://offline.test")
        await http_transport.close()
        with pytest.raises(RuntimeError, match="closed"):
            await http_transport.get("https://offline.test")
        await client.aclose()

    asyncio.run(exercise())
