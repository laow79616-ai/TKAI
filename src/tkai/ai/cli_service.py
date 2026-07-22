"""Read-only service facade used by the AI command-line interface."""

from __future__ import annotations

import platform
from collections.abc import Iterable
from typing import Any

from tkai import __version__
from tkai.configuration import ConfigurationManager
from tkai.credentials import CredentialManager

from .doctor import DoctorReport, DoctorService
from .fallback import FallbackCandidate, FallbackEngine, FallbackPolicy
from .manager import ProviderManager
from .models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)


class AICommandService:
    """Aggregate existing AI services for thin, provider-agnostic CLI commands."""

    def __init__(
        self,
        manager: ProviderManager | None = None,
        *,
        fallback: FallbackEngine | FallbackPolicy | None = None,
        fallback_candidates: Iterable[FallbackCandidate[object]] = (),
        credentials: CredentialManager | None = None,
        configuration: ConfigurationManager | None = None,
    ) -> None:
        self.manager = manager or ProviderManager()
        self.fallback = fallback or FallbackEngine()
        self.fallback_candidates = tuple(fallback_candidates)
        self.credentials = credentials
        self.configuration = configuration

    def configuration_summary(self) -> dict[str, Any]:
        """Return immutable resolved configuration metadata without secrets."""
        if self.configuration is None:
            return {
                "source": "default",
                "overrides": [],
                "application": {},
                "runtime": {},
                "providers": {},
            }
        config = self.configuration.list()
        return {
            "source": config.source,
            "overrides": list(config.overrides),
            "application": config.get("application", {}),
            "runtime": config.get("runtime", {}),
            "providers": config.get("providers", config.get("provider", {})),
            "loaded_files": [
                item for item in config.overrides if item in {"workspace", "user"}
            ],
        }

    def credentials_summary(self) -> list[dict[str, object]]:
        """Return safe local credential metadata without API key values."""
        if self.credentials is None:
            return []
        return [
            {
                "provider": item.provider,
                "configured": True,
                "source": item.source,
                "masked": item.masked(),
            }
            for item in self.credentials.list()
        ]

    def doctor(self) -> DoctorReport:
        """Run the complete read-only diagnostic suite."""
        return self._doctor_service().run()

    def validate_config(self) -> DoctorReport:
        """Run only provider registry, configuration, and capability diagnostics."""
        return self._doctor_service().validate_config()

    def providers(self) -> list[dict[str, Any]]:
        """Return safe provider summaries from the manager's registry metadata."""
        aliases = self.manager.aliases()
        summaries: list[dict[str, Any]] = []
        for name in self.manager.names():
            capabilities = self.manager.registry.capabilities_for(name)
            model_capabilities = self.manager.model_capabilities(name)
            summaries.append(
                {
                    "provider": name,
                    "aliases": sorted(
                        alias for alias, target in aliases.items() if target == name
                    ),
                    "default": name == self.manager.default_provider,
                    "capabilities": sorted(
                        capability.value for capability in capabilities.supported()
                    ),
                    "model_count": len(model_capabilities),
                }
            )
        return summaries

    def provider(self, name: str) -> dict[str, Any]:
        """Return one provider summary while resolving registered aliases."""
        canonical_name = self.manager.registry.resolve(name)
        for item in self.providers():
            if item["provider"] == canonical_name:
                return item
        self.manager.get(name)
        raise AssertionError("registered provider summary was not found")

    def models(self, name: str | None = None) -> list[str]:
        """Return model identifiers from the selected manager-owned provider."""
        return [model.id for model in self.manager.get(name).list_models()]

    def chat(
        self, message: str, *, provider: str | None = None, model: str | None = None
    ) -> ChatResponse:
        """Route a compatibility chat request through the existing manager."""
        return self.manager.chat(
            ChatRequest((ChatMessage("user", message),), model), provider=provider
        )

    def embed(
        self, text: str, *, provider: str | None = None, model: str | None = None
    ) -> EmbeddingResponse:
        """Route a compatibility embedding request through the existing manager."""
        return self.manager.embed(EmbeddingRequest((text,), model), provider=provider)

    def capabilities(
        self, *, provider: str | None = None, model: str | None = None
    ) -> list[dict[str, Any]]:
        """Return provider defaults and exact model capability overrides."""
        names = (
            [self.manager.registry.resolve(provider)]
            if provider
            else self.manager.names()
        )
        result: list[dict[str, Any]] = []
        for name in names:
            self.manager.get(name)
            model_capabilities = self.manager.model_capabilities(name)
            if model is not None:
                capabilities = self.manager.registry.capabilities_for(name, model)
                result.append(
                    {
                        "provider": name,
                        "model": model,
                        "override": model in model_capabilities,
                        "capabilities": sorted(
                            capability.value for capability in capabilities.supported()
                        ),
                    }
                )
                continue
            defaults = self.manager.registry.capabilities_for(name)
            result.append(
                {
                    "provider": name,
                    "model": None,
                    "override": False,
                    "capabilities": sorted(
                        capability.value for capability in defaults.supported()
                    ),
                    "model_overrides": {
                        key: sorted(item.value for item in value.supported())
                        for key, value in model_capabilities.items()
                    },
                }
            )
        return result

    def fallback_summary(self) -> dict[str, Any]:
        """Return fallback policy and ordered candidate metadata without execution."""
        policy = self._fallback_policy()
        return {
            "max_attempts": policy.max_attempts,
            "retry_budget": policy.retry_budget,
            "blacklist": sorted(policy.blocked_providers),
            "candidate_order": [
                candidate.name for candidate in self.fallback_candidates
            ],
        }

    def version(self) -> dict[str, str]:
        """Return framework and local runtime version metadata."""
        return {
            "tkai_version": __version__,
            "python_version": platform.python_version(),
            "runtime_version": platform.python_implementation(),
        }

    def info(self) -> dict[str, Any]:
        """Return a framework-level read-only summary using existing services."""
        report = self.doctor()
        runtime_checks = [
            check.name for check in report.checks if check.name.startswith("runtime")
        ]
        transport_checks = [
            check.name for check in report.checks if check.name.startswith("transport")
        ]
        return {
            "registered_providers": self.manager.names(),
            "default_provider": self.manager.default_provider,
            "runtime_checks": runtime_checks,
            "transport_checks": transport_checks,
            "capabilities": self.capabilities(),
            "fallback": self.fallback_summary(),
        }

    def _doctor_service(self) -> DoctorService:
        """Create a stateless doctor facade over the existing service objects."""
        return DoctorService(
            self.manager,
            fallback=self.fallback,
            fallback_candidates=self.fallback_candidates,
            credentials=self.credentials,
            persistent_configuration=self.configuration,
        )

    def _fallback_policy(self) -> FallbackPolicy:
        """Expose an existing fallback policy without executing fallback work."""
        if isinstance(self.fallback, FallbackEngine):
            return self.fallback.policy
        return self.fallback
