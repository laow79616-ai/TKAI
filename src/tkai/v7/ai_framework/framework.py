"""Unified AI metadata framework; intentionally incapable of model execution."""

from __future__ import annotations

from collections import Counter
from string import Formatter
from threading import RLock
from typing import TypeVar

from .contracts import (
    AIModel,
    Evaluation,
    GovernanceRecord,
    Lifecycle,
    PromptTemplate,
    ProviderDefinition,
    ReasoningSession,
    ReviewStatus,
    RiskClass,
    RouteDecision,
    RouteRequest,
    SafetyPolicy,
    Scope,
    serialize,
)

T = TypeVar("T")
MAX_RECORDS = 1000


class AIFrameworkError(RuntimeError):
    pass


class DuplicateReferenceError(AIFrameworkError):
    pass


class IsolationError(AIFrameworkError):
    pass


class MetadataStore:
    def __init__(self) -> None:
        self._values: dict[str, object] = {}
        self._lock = RLock()

    def register(self, key: str, value: T) -> T:
        with self._lock:
            if key in self._values:
                raise DuplicateReferenceError(f"already registered: {key}")
            if len(self._values) >= MAX_RECORDS:
                raise AIFrameworkError("metadata store capacity reached")
            self._values[key] = value
        return value

    def values(self, expected: type[T], scope: Scope | None = None) -> tuple[T, ...]:
        items = tuple(v for v in self._values.values() if isinstance(v, expected))
        if scope is not None:
            items = tuple(v for v in items if getattr(v, "scope", None) == scope)
        return items[:MAX_RECORDS]


class UnifiedAIFramework:
    """Coordinates scoped AI metadata and contracts without invoking providers."""

    def __init__(self) -> None:
        self.providers = MetadataStore()
        self.models = MetadataStore()
        self.templates = MetadataStore()
        self.sessions = MetadataStore()
        self.evaluations = MetadataStore()
        self.governance = MetadataStore()
        self.safety = MetadataStore()
        self.audit: list[dict[str, object]] = []
        self.traces: list[dict[str, object]] = []
        self.metrics: Counter[str] = Counter()

    def register_provider(self, item: ProviderDefinition) -> ProviderDefinition:
        return self._register(self.providers, item.provider_id, item, "provider")

    def register_model(self, item: AIModel) -> AIModel:
        if item.provider_id not in {
            provider.provider_id
            for provider in self.providers.values(ProviderDefinition, item.scope)
        }:
            raise AIFrameworkError("provider is not registered in model scope")
        return self._register(self.models, item.model_id, item, "model")

    def register_template(self, item: PromptTemplate) -> PromptTemplate:
        fields = {
            field_name
            for _, field_name, _, _ in Formatter().parse(item.template)
            if field_name
        }
        missing = set(item.variables) - fields
        if missing:
            raise AIFrameworkError(
                f"template variables are not referenced: {sorted(missing)}"
            )
        return self._register(
            self.templates, f"{item.template_id}:{item.version}", item, "template"
        )

    def register_session(self, item: ReasoningSession) -> ReasoningSession:
        return self._register(self.sessions, item.session_id, item, "session")

    def register_evaluation(self, item: Evaluation) -> Evaluation:
        return self._register(self.evaluations, item.evaluation_id, item, "evaluation")

    def register_governance(self, item: GovernanceRecord) -> GovernanceRecord:
        return self._register(self.governance, item.governance_id, item, "governance")

    def register_safety_policy(self, item: SafetyPolicy) -> SafetyPolicy:
        return self._register(self.safety, item.policy_id, item, "safety")

    def route(self, request: RouteRequest) -> RouteDecision:
        candidates = [
            model
            for model in self.models.values(AIModel, request.scope)
            if model.lifecycle is Lifecycle.ACTIVE
            and request.required_capabilities.issubset(model.capabilities)
            and request.required_modalities.issubset(model.supported_modalities)
            and (
                not request.compatible_versions
                or model.version in request.compatible_versions
            )
            and self._approved(model, request.scope)
        ]
        candidates.sort(
            key=lambda model: (
                -self._evaluation_score(model, request.scope),
                model.model_id,
            )
        )
        ids = tuple(model.model_id for model in candidates)
        self.metrics["v7_ai_route_decisions_total"] += 1
        self._record("route", ids[0] if ids else "none", request.scope)
        return RouteDecision(
            ids[0] if ids else None,
            ids,
            ids[1:],
            "metadata-match" if ids else "no-compatible-approved-model",
        )

    def projection(self, section: str, scope: Scope) -> object:
        mapping: dict[str, object] = {
            "providers": self.providers.values(ProviderDefinition, scope),
            "models": self.models.values(AIModel, scope),
            "templates": self.templates.values(PromptTemplate, scope),
            "sessions": self.sessions.values(ReasoningSession, scope),
            "evaluation": self.evaluations.values(Evaluation, scope),
            "governance": self.governance.values(GovernanceRecord, scope),
            "safety": self.safety.values(SafetyPolicy, scope),
            "metrics": dict(self.metrics),
            "audit": tuple(
                event for event in self.audit if event["scope"] == serialize(scope)
            ),
        }
        if section not in mapping:
            raise AIFrameworkError(f"unknown projection: {section}")
        return serialize(mapping[section])

    def health(self, scope: Scope) -> dict[str, object]:
        return {
            "status": "healthy",
            "providers": len(self.providers.values(ProviderDefinition, scope)),
            "models": len(self.models.values(AIModel, scope)),
            "execution_enabled": False,
            "external_calls_enabled": False,
        }

    def _approved(self, model: AIModel, scope: Scope) -> bool:
        governance_approved = any(
            item.subject_reference == model.model_id
            and item.approval_status is ReviewStatus.APPROVED
            for item in self.governance.values(GovernanceRecord, scope)
        )
        policies = {
            item.policy_id: item for item in self.safety.values(SafetyPolicy, scope)
        }
        safety_approved = bool(model.safety_policy_references) and all(
            reference in policies
            and policies[reference].review_status is ReviewStatus.APPROVED
            and policies[reference].risk_classification is not RiskClass.PROHIBITED
            for reference in model.safety_policy_references
        )
        return governance_approved and safety_approved

    def _evaluation_score(self, model: AIModel, scope: Scope) -> float:
        values = [
            (item.quality_score + item.compatibility_score + item.safety_score) / 3
            for item in self.evaluations.values(Evaluation, scope)
            if item.model_id == model.model_id
        ]
        return max(values, default=0)

    def _register(self, store: MetadataStore, key: str, item: T, kind: str) -> T:
        result = store.register(key, item)
        self.metrics[f"v7_ai_{kind}s_registered_total"] += 1
        scope = getattr(item, "scope")  # noqa: B009 - generic metadata contract
        if not isinstance(scope, Scope):
            raise AIFrameworkError("registered metadata must have a scope")
        self._record(f"{kind}-registered", key, scope)
        return result

    def _record(self, action: str, subject: str, scope: Scope) -> None:
        event = {"action": action, "subject": subject, "scope": serialize(scope)}
        self.audit.append(event)
        self.traces.append({"hook": "v7.ai_framework", **event})


GLOBAL_AI_FRAMEWORK = UnifiedAIFramework()
__all__ = (
    "AIFrameworkError",
    "DuplicateReferenceError",
    "GLOBAL_AI_FRAMEWORK",
    "IsolationError",
    "MetadataStore",
    "UnifiedAIFramework",
)
