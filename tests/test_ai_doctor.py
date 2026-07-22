"""Offline, read-only coverage for the AI provider doctor framework."""

from __future__ import annotations

from typing import Any

from tkai.ai import (
    AIResponse,
    BaseAIProvider,
    DoctorService,
    DoctorStatus,
    FallbackCandidate,
    FallbackPolicy,
    ProviderCapabilities,
    ProviderConfig,
    ProviderManager,
)
from tkai.ai.runtime import OwnershipPolicy, ProviderRuntime
from tkai.ai.sync_bridge import SyncBridge
from tkai.ai.transport_adapter import TransportAdapter


class DoctorProvider(BaseAIProvider):
    """Small offline provider with configuration and runtime diagnostic fields."""

    name = "doctor"
    default_model = "doctor-model"
    capabilities = ProviderCapabilities(chat=True, streaming=True, async_=True)

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__()
        self.config = config

    def generate(
        self, prompt: str, *, model: str | None = None, **options: Any
    ) -> AIResponse:
        return AIResponse(prompt, self.name, model or self.default_model)


class FakeTransport:
    """Protocol-shaped offline transport that records no activity."""

    async def request(self, *args: object, **kwargs: object) -> dict[str, object]:
        return {}

    async def stream(self, *args: object, **kwargs: object):
        if False:
            yield b""

    async def close(self) -> None:
        return None


def check(report, name: str):
    """Return one named report check for concise assertions."""
    return next(item for item in report.checks if item.name == name)


def test_environment_report_has_pass_json_and_text_output() -> None:
    report = DoctorService().run()

    assert check(report, "environment.python").status is DoctorStatus.PASS
    assert check(report, "provider.registry").status is DoctorStatus.WARNING
    assert '"checks"' in report.to_json()
    assert "TKAI AI Doctor" in report.to_text()


def test_provider_configuration_capabilities_and_secret_redaction() -> None:
    manager = ProviderManager()
    provider = DoctorProvider(
        ProviderConfig(
            name="doctor",
            type="openai-compatible",
            api_key="super-secret-api-key",
            base_url="https://example.test",
            model="doctor-model",
        )
    )
    manager.register(
        provider,
        default=True,
        aliases=("primary",),
        model_capabilities={
            "doctor-model": ProviderCapabilities(chat=True, vision=True)
        },
    )

    report = DoctorService(manager).run()

    assert check(report, "provider.registry").status is DoctorStatus.PASS
    assert check(report, "configuration.doctor").status is DoctorStatus.PASS
    assert check(report, "capability.doctor").status is DoctorStatus.PASS
    assert "super-secret-api-key" not in report.to_json()
    assert "super-secret-api-key" not in report.to_text()


def test_invalid_configuration_and_provider_default_are_errors() -> None:
    manager = ProviderManager()
    manager.register(
        DoctorProvider(ProviderConfig(name="doctor", type="openai", timeout=-1)),
        default=True,
    )
    manager.default_provider = "missing"

    report = DoctorService(manager).run()

    assert check(report, "provider.registry").status is DoctorStatus.ERROR
    assert check(report, "configuration.doctor").status is DoctorStatus.ERROR


def test_transport_runtime_and_fallback_checks_are_read_only() -> None:
    def callback(
        path: str, payload: dict[str, object], headers: dict[str, str]
    ) -> dict[str, object]:
        return {"choices": []}

    adapter = TransportAdapter(callback)
    runtime = ProviderRuntime(FakeTransport(), ownership=OwnershipPolicy.RUNTIME_OWNED)
    bridge = SyncBridge()
    policy = FallbackPolicy(max_attempts=2, retry_budget=1)
    report = DoctorService(
        transports=(callback, adapter),
        runtimes=(runtime,),
        adapters=(object(),),
        bridges=(bridge,),
        fallback=policy,
        fallback_candidates=(
            FallbackCandidate("primary", object()),
            FallbackCandidate("backup", object()),
        ),
    ).run()

    assert check(report, "transport.0").status is DoctorStatus.PASS
    assert check(report, "transport.1").status is DoctorStatus.PASS
    assert check(report, "runtime.0").status is DoctorStatus.PASS
    assert check(report, "runtime.adapter").status is DoctorStatus.PASS
    assert check(report, "runtime.sync_bridge").status is DoctorStatus.PASS
    assert check(report, "fallback").status is DoctorStatus.PASS
    assert runtime.state.name == "CREATED"
    assert not adapter._closed


def test_fallback_warnings_and_errors_are_reported() -> None:
    all_blocked = FallbackPolicy(blocked_providers=frozenset({"primary"}))
    warning = DoctorService(
        fallback=all_blocked,
        fallback_candidates=(FallbackCandidate("primary", object()),),
    ).run()
    duplicate = DoctorService(
        fallback=FallbackPolicy(),
        fallback_candidates=(
            FallbackCandidate("primary", object()),
            FallbackCandidate("primary", object()),
        ),
    ).run()

    assert check(warning, "fallback").status is DoctorStatus.WARNING
    assert check(duplicate, "fallback").status is DoctorStatus.ERROR
