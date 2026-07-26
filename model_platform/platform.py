"""Enterprise AI Model Platform domain services.

The module is intentionally provider-SDK agnostic. Provider integrations receive
credential references, never secret material, and may be implemented by a host.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from time import monotonic
from typing import Any, Protocol


class ModelStatus(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    VALIDATED = "validated"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class DeploymentKind(str, Enum):
    HOSTED = "hosted"
    EXTERNAL_API = "external_api"
    LOCAL = "local"
    KUBERNETES = "kubernetes"


class HealthStatus(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class FailureKind(str, Enum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    POLICY = "policy"
    QUOTA = "quota"
    PROVIDER = "provider"
    INVALID_REQUEST = "invalid_request"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ModelScope:
    tenant: str
    workspace: str
    actor: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class ModelRecord:
    id: str
    name: str
    provider: str
    version: str
    capabilities: tuple[str, ...]
    context_window: int
    input_types: tuple[str, ...]
    output_types: tuple[str, ...]
    tenant: str
    workspace: str
    status: ModelStatus = ModelStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(frozen=True, slots=True)
class ProviderConfiguration:
    id: str
    provider_type: str
    credential_reference: str | None = None
    endpoint: str | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        supported = {
            "openai",
            "anthropic",
            "gemini",
            "azure_openai",
            "ollama",
            "local",
            "custom",
        }
        if self.provider_type not in supported:
            raise ValueError(f"Unsupported provider type: {self.provider_type}")
        forbidden = {"api_key", "secret", "password", "token", "credential"}
        if forbidden & {key.casefold() for key in self.metadata}:
            raise ValueError("Provider metadata must not contain credentials.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Provider(Protocol):
    """Host-supplied provider interface."""

    def invoke(self, model: ModelRecord, request: dict[str, Any]) -> dict[str, Any]: ...
    def health(self) -> HealthStatus: ...


class LocalProvider(Protocol):
    def load(self, reference: str) -> None: ...
    def invoke(self, model: ModelRecord, request: dict[str, Any]) -> dict[str, Any]: ...


class CustomProvider(Provider, Protocol):
    """Extension interface for enterprise-specific providers."""


@dataclass(frozen=True, slots=True)
class ModelProfile:
    id: str
    name: str
    tenant: str
    workspace: str
    default_model: str
    fallback_models: tuple[str, ...] = ()
    temperature: float = 0.0
    token_limit: int = 4096
    timeout_seconds: float = 30.0
    retries: int = 1
    capabilities: tuple[str, ...] = ()
    use_cases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2.")
        if self.token_limit <= 0 or self.timeout_seconds <= 0 or self.retries < 0:
            raise ValueError(
                "Profile limits must be positive and retries non-negative."
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RouteRequest:
    tenant: str
    workspace: str
    capability: str = ""
    use_case: str = ""
    provider: str | None = None
    model: str | None = None
    max_estimated_cost: float | None = None
    max_latency_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class RoutingRule:
    id: str
    priority: int
    model_id: str
    provider: str | None = None
    capability: str | None = None
    tenant: str | None = None
    workspace: str | None = None
    max_cost: float | None = None
    max_latency_seconds: float | None = None
    policy: str | None = None
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ScalingConfiguration:
    minimum_replicas: int = 1
    maximum_replicas: int = 1
    target_concurrency: int = 1

    def __post_init__(self) -> None:
        if (
            self.minimum_replicas < 0
            or self.maximum_replicas < self.minimum_replicas
            or self.target_concurrency <= 0
        ):
            raise ValueError("Invalid scaling configuration.")


@dataclass(slots=True)
class ModelDeployment:
    id: str
    model_id: str
    tenant: str
    workspace: str
    kind: DeploymentKind
    reference: str
    scaling: ScalingConfiguration = field(default_factory=ScalingConfiguration)
    health: HealthStatus = HealthStatus.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["kind"] = self.kind.value
        value["health"] = self.health.value
        return value


class KubernetesDeployment(Protocol):
    def deploy(
        self, deployment: ModelDeployment, scaling: ScalingConfiguration
    ) -> str: ...
    def scale(self, reference: str, replicas: int) -> None: ...
    def health(self, reference: str) -> HealthStatus: ...


@dataclass(frozen=True, slots=True)
class EvaluationRecord:
    id: str
    model_id: str
    tenant: str
    workspace: str
    quality: float
    latency_seconds: float
    reliability: float
    cost_estimate: float
    accuracy: float | None = None
    safety: float | None = None
    regression: bool = False
    baseline_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AccuracyEvaluator(Protocol):
    def evaluate(self, expected: tuple[Any, ...], actual: tuple[Any, ...]) -> float: ...


class SafetyEvaluator(Protocol):
    def evaluate(self, inputs: tuple[Any, ...], outputs: tuple[Any, ...]) -> float: ...


@dataclass(frozen=True, slots=True)
class BenchmarkRecord:
    id: str
    model_id: str
    tenant: str
    workspace: str
    dataset_reference: str
    scenario: str
    score: float
    latency_seconds: float
    token_usage: int
    estimated_cost: float | None = None
    model_version: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CostCalculator(Protocol):
    def estimate(
        self, provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> float: ...


@dataclass(frozen=True, slots=True)
class Quota:
    tenant: str
    workspace: str
    request_limit: int | None = None
    token_limit: int | None = None
    concurrency_limit: int | None = None
    rate_limit: int | None = None


@dataclass(frozen=True, slots=True)
class UsageRecord:
    id: str
    model_id: str
    provider: str
    tenant: str
    workspace: str
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    estimated_cost: float = 0.0
    actual_cost: float | None = None
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProviderPricing(Protocol):
    def estimate(self, model: str, input_tokens: int, output_tokens: int) -> float: ...


class ActualUsage(Protocol):
    def actual_cost(self, usage_id: str) -> float | None: ...


@dataclass(frozen=True, slots=True)
class Budget:
    tenant: str
    workspace: str
    limit: float
    alert_thresholds: tuple[float, ...] = (0.8, 1.0)


@dataclass(frozen=True, slots=True)
class GovernanceRecord:
    model_id: str
    tenant: str
    workspace: str
    approval_status: str
    allowed_use: tuple[str, ...] = ()
    restricted_use: tuple[str, ...] = ()
    risk_classification: str = "unclassified"
    evaluation_reference: str | None = None
    policy_mapping: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuditEvent:
    action: str
    resource: str
    tenant: str
    workspace: str
    actor: str
    outcome: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelSecurity:
    def __init__(self) -> None:
        self._grants: dict[tuple[str, str, str], set[str]] = {}
        self.provider_allowlist: dict[tuple[str, str], set[str]] = {}
        self.model_allowlist: dict[tuple[str, str], set[str]] = {}
        self.audit_events: list[AuditEvent] = []

    def grant(self, scope: ModelScope, permissions: set[str]) -> None:
        self._grants.setdefault(
            (scope.tenant, scope.workspace, scope.actor), set()
        ).update(permissions)

    def authorize(self, scope: ModelScope, permission: str) -> None:
        grants = self._grants.get((scope.tenant, scope.workspace, scope.actor), set())
        if permission not in grants and "models:admin" not in grants:
            raise PermissionError(f"Missing permission: {permission}")

    @staticmethod
    def isolate(tenant: str, workspace: str, scope: ModelScope) -> None:
        if tenant != scope.tenant:
            raise PermissionError("Cross-tenant model access denied.")
        if workspace != scope.workspace:
            raise PermissionError("Cross-workspace model access denied.")

    def allowed(self, provider: str, model_id: str, scope: ModelScope) -> None:
        key = (scope.tenant, scope.workspace)
        providers = self.provider_allowlist.get(key)
        models = self.model_allowlist.get(key)
        if providers is not None and provider not in providers:
            raise PermissionError("Provider is not allowed.")
        if models is not None and model_id not in models:
            raise PermissionError("Model is not allowed.")

    def audit(self, event: AuditEvent) -> None:
        forbidden = {"secret", "token", "password", "api_key", "credential"}
        safe = {
            key: value
            for key, value in event.metadata.items()
            if key.casefold() not in forbidden
        }
        self.audit_events.append(replace(event, metadata=safe))


METRICS = (
    "models_total",
    "model_requests_total",
    "model_failures_total",
    "model_fallback_total",
    "model_latency_seconds",
    "model_tokens_total",
    "model_cost_estimate_total",
    "model_quota_rejections_total",
)


class ModelMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = {name: 0.0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in self.values:
            raise ValueError(f"Unknown model metric: {name}")
        self.values[name] += amount

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{name} {value}\n" for name, value in self.values.items())


TRANSITIONS: dict[ModelStatus, set[ModelStatus]] = {
    ModelStatus.DRAFT: {ModelStatus.REGISTERED, ModelStatus.ARCHIVED},
    ModelStatus.REGISTERED: {ModelStatus.VALIDATED, ModelStatus.ARCHIVED},
    ModelStatus.VALIDATED: {ModelStatus.APPROVED, ModelStatus.SUSPENDED},
    ModelStatus.APPROVED: {ModelStatus.ACTIVE, ModelStatus.SUSPENDED},
    ModelStatus.ACTIVE: {
        ModelStatus.DEPRECATED,
        ModelStatus.SUSPENDED,
    },
    ModelStatus.DEPRECATED: {ModelStatus.ARCHIVED, ModelStatus.SUSPENDED},
    ModelStatus.SUSPENDED: {ModelStatus.APPROVED, ModelStatus.ARCHIVED},
    ModelStatus.ARCHIVED: set(),
}

DASHBOARD_SECTIONS = (
    "model-registry",
    "providers",
    "profiles",
    "deployments",
    "routing",
    "fallback",
    "evaluation",
    "benchmarks",
    "usage",
    "cost",
    "governance",
)


class ModelPlatform:
    def __init__(self) -> None:
        self.models: dict[str, ModelRecord] = {}
        self.providers: dict[str, ProviderConfiguration] = {}
        self.provider_adapters: dict[str, Provider] = {}
        self.profiles: dict[str, ModelProfile] = {}
        self.deployments: dict[str, ModelDeployment] = {}
        self.routes: dict[str, RoutingRule] = {}
        self.evaluations: dict[str, EvaluationRecord] = {}
        self.benchmarks: dict[str, BenchmarkRecord] = {}
        self.quotas: dict[tuple[str, str], Quota] = {}
        self.usage: list[UsageRecord] = []
        self.budgets: dict[tuple[str, str], Budget] = {}
        self.governance: dict[str, GovernanceRecord] = {}
        self.security = ModelSecurity()
        self.metrics = ModelMetrics()

    def register_model(self, payload: dict[str, Any], scope: ModelScope) -> ModelRecord:
        self.security.authorize(scope, "models:write")
        model_id = str(payload["id"])
        if model_id in self.models:
            raise ValueError(f"Model already exists: {model_id}")
        model = ModelRecord(
            id=model_id,
            name=str(payload["name"]),
            provider=str(payload["provider"]),
            version=str(payload["version"]),
            capabilities=tuple(payload.get("capabilities", ())),
            context_window=int(payload["context_window"]),
            input_types=tuple(payload.get("input_types", ("text",))),
            output_types=tuple(payload.get("output_types", ("text",))),
            tenant=scope.tenant,
            workspace=scope.workspace,
            metadata=dict(payload.get("metadata", {})),
        )
        if model.context_window <= 0:
            raise ValueError("Context window must be positive.")
        self.models[model_id] = model
        self.metrics.increment("models_total")
        self.security.audit(
            AuditEvent(
                "model.register",
                model_id,
                scope.tenant,
                scope.workspace,
                scope.actor,
                "success",
            )
        )
        return model

    def get_model(self, model_id: str, scope: ModelScope) -> ModelRecord:
        self.security.authorize(scope, "models:read")
        model = self.models[model_id]
        self.security.isolate(model.tenant, model.workspace, scope)
        return model

    def list_models(self, scope: ModelScope) -> tuple[ModelRecord, ...]:
        self.security.authorize(scope, "models:read")
        return tuple(
            model
            for model in self.models.values()
            if model.tenant == scope.tenant and model.workspace == scope.workspace
        )

    def transition(self, model_id: str, status: str, scope: ModelScope) -> ModelRecord:
        self.security.authorize(scope, "models:approve")
        model = self.get_model(model_id, scope)
        target = ModelStatus(status)
        if target not in TRANSITIONS[model.status]:
            raise ValueError(
                f"Invalid model transition: {model.status.value} -> {target.value}"
            )
        updated = replace(model, status=target)
        self.models[model_id] = updated
        return updated

    def add_provider(
        self, configuration: ProviderConfiguration, scope: ModelScope
    ) -> ProviderConfiguration:
        self.security.authorize(scope, "models:admin")
        if configuration.id in self.providers:
            raise ValueError(f"Provider already exists: {configuration.id}")
        self.providers[configuration.id] = configuration
        return configuration

    def bind_provider(self, provider_id: str, adapter: Provider) -> None:
        if provider_id not in self.providers:
            raise KeyError(f"Provider not configured: {provider_id}")
        self.provider_adapters[provider_id] = adapter

    def add_profile(self, profile: ModelProfile, scope: ModelScope) -> ModelProfile:
        self.security.authorize(scope, "models:write")
        self.security.isolate(profile.tenant, profile.workspace, scope)
        for model_id in (profile.default_model, *profile.fallback_models):
            self.get_model(model_id, scope)
        self.profiles[profile.id] = profile
        return profile

    def add_route(self, rule: RoutingRule, scope: ModelScope) -> RoutingRule:
        self.security.authorize(scope, "models:route")
        model = self.get_model(rule.model_id, scope)
        self.security.allowed(model.provider, model.id, scope)
        self.routes[rule.id] = rule
        return rule

    def route(self, request: RouteRequest, scope: ModelScope) -> ModelRecord:
        self.security.authorize(scope, "models:route")
        if (request.tenant, request.workspace) != (scope.tenant, scope.workspace):
            raise PermissionError("Route scope does not match caller scope.")
        matches: list[RoutingRule] = []
        for rule in self.routes.values():
            if not rule.enabled:
                continue
            model = self.get_model(rule.model_id, scope)
            if model.status is not ModelStatus.ACTIVE:
                continue
            checks = (
                rule.tenant is None or rule.tenant == request.tenant,
                rule.workspace is None or rule.workspace == request.workspace,
                rule.provider is None
                or rule.provider == (request.provider or model.provider),
                rule.capability is None or rule.capability == request.capability,
                request.model is None or request.model == rule.model_id,
                request.max_estimated_cost is None
                or rule.max_cost is None
                or rule.max_cost <= request.max_estimated_cost,
                request.max_latency_seconds is None
                or rule.max_latency_seconds is None
                or rule.max_latency_seconds <= request.max_latency_seconds,
            )
            if all(checks):
                matches.append(rule)
        if not matches:
            raise LookupError("No model route matched the request.")
        selected = min(matches, key=lambda item: (item.priority, item.id))
        model = self.get_model(selected.model_id, scope)
        self.security.allowed(model.provider, model.id, scope)
        governance = self.governance.get(model.id)
        if selected.policy and (
            governance is None or selected.policy not in governance.policy_mapping
        ):
            raise PermissionError("Model route policy is not satisfied.")
        return model

    def add_deployment(
        self, deployment: ModelDeployment, scope: ModelScope
    ) -> ModelDeployment:
        self.security.authorize(scope, "models:deploy")
        self.security.isolate(deployment.tenant, deployment.workspace, scope)
        self.get_model(deployment.model_id, scope)
        self.deployments[deployment.id] = deployment
        return deployment

    def set_deployment_health(
        self, deployment_id: str, health: HealthStatus, scope: ModelScope
    ) -> ModelDeployment:
        deployment = self.deployments[deployment_id]
        self.security.isolate(deployment.tenant, deployment.workspace, scope)
        deployment.health = health
        return deployment

    def add_evaluation(
        self, record: EvaluationRecord, scope: ModelScope
    ) -> EvaluationRecord:
        self.security.authorize(scope, "models:evaluate")
        self.security.isolate(record.tenant, record.workspace, scope)
        self.get_model(record.model_id, scope)
        self.evaluations[record.id] = record
        return record

    def compare_evaluations(self, left: str, right: str) -> dict[str, float]:
        a, b = self.evaluations[left], self.evaluations[right]
        return {
            "quality": b.quality - a.quality,
            "latency_seconds": b.latency_seconds - a.latency_seconds,
            "reliability": b.reliability - a.reliability,
            "cost_estimate": b.cost_estimate - a.cost_estimate,
        }

    def add_benchmark(
        self, record: BenchmarkRecord, scope: ModelScope
    ) -> BenchmarkRecord:
        self.security.authorize(scope, "models:evaluate")
        self.security.isolate(record.tenant, record.workspace, scope)
        self.get_model(record.model_id, scope)
        self.benchmarks[record.id] = record
        return record

    def compare_versions(self, left: str, right: str) -> dict[str, float]:
        a, b = self.benchmarks[left], self.benchmarks[right]
        return {
            "score": b.score - a.score,
            "latency_seconds": b.latency_seconds - a.latency_seconds,
            "token_usage": float(b.token_usage - a.token_usage),
            "estimated_cost": (b.estimated_cost or 0) - (a.estimated_cost or 0),
        }

    def set_quota(self, quota: Quota, scope: ModelScope) -> Quota:
        self.security.authorize(scope, "models:admin")
        self.security.isolate(quota.tenant, quota.workspace, scope)
        self.quotas[(quota.tenant, quota.workspace)] = quota
        return quota

    def check_quota(
        self, scope: ModelScope, requested_tokens: int = 0, concurrency: int = 1
    ) -> None:
        quota = self.quotas.get((scope.tenant, scope.workspace))
        if quota is None:
            return
        records = [
            item
            for item in self.usage
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]
        rejected = (
            (quota.request_limit is not None and len(records) >= quota.request_limit)
            or (
                quota.token_limit is not None
                and sum(item.input_tokens + item.output_tokens for item in records)
                + requested_tokens
                > quota.token_limit
            )
            or (
                quota.concurrency_limit is not None
                and concurrency > quota.concurrency_limit
            )
            or (quota.rate_limit is not None and len(records) >= quota.rate_limit)
        )
        if rejected:
            self.metrics.increment("model_quota_rejections_total")
            raise PermissionError("Model quota exceeded.")

    def record_usage(self, record: UsageRecord, scope: ModelScope) -> UsageRecord:
        self.security.isolate(record.tenant, record.workspace, scope)
        self.usage.append(record)
        self.metrics.increment("model_requests_total")
        self.metrics.increment(
            "model_tokens_total", record.input_tokens + record.output_tokens
        )
        self.metrics.increment("model_latency_seconds", record.latency_seconds)
        self.metrics.increment("model_cost_estimate_total", record.estimated_cost)
        if not record.success:
            self.metrics.increment("model_failures_total")
        return record

    def set_budget(self, budget: Budget, scope: ModelScope) -> Budget:
        self.security.authorize(scope, "models:admin")
        self.security.isolate(budget.tenant, budget.workspace, scope)
        if budget.limit < 0:
            raise ValueError("Budget cannot be negative.")
        self.budgets[(budget.tenant, budget.workspace)] = budget
        return budget

    def budget_status(self, scope: ModelScope) -> dict[str, Any]:
        budget = self.budgets.get((scope.tenant, scope.workspace))
        total = sum(
            item.actual_cost if item.actual_cost is not None else item.estimated_cost
            for item in self.usage
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        )
        if budget is None:
            return {"spent": total, "limit": None, "alerts": ()}
        ratio = total / budget.limit if budget.limit else float("inf")
        return {
            "spent": total,
            "limit": budget.limit,
            "alerts": tuple(
                value for value in budget.alert_thresholds if ratio >= value
            ),
        }

    def set_governance(
        self, record: GovernanceRecord, scope: ModelScope
    ) -> GovernanceRecord:
        self.security.authorize(scope, "models:govern")
        self.security.isolate(record.tenant, record.workspace, scope)
        self.get_model(record.model_id, scope)
        self.governance[record.model_id] = record
        return record

    @staticmethod
    def classify_failure(error: Exception) -> FailureKind:
        message = str(error).casefold()
        if isinstance(error, TimeoutError) or "timeout" in message:
            return FailureKind.TIMEOUT
        if "rate" in message and "limit" in message:
            return FailureKind.RATE_LIMIT
        if "auth" in message or "credential" in message:
            return FailureKind.AUTHENTICATION
        if "policy" in message or isinstance(error, PermissionError):
            return FailureKind.POLICY
        if isinstance(error, ValueError):
            return FailureKind.INVALID_REQUEST
        if isinstance(error, ConnectionError):
            return FailureKind.PROVIDER
        return FailureKind.UNKNOWN

    def invoke(
        self,
        profile_id: str,
        request: dict[str, Any],
        scope: ModelScope,
        *,
        max_attempts: int | None = None,
    ) -> dict[str, Any]:
        self.security.authorize(scope, "models:invoke")
        profile = self.profiles[profile_id]
        self.security.isolate(profile.tenant, profile.workspace, scope)
        requested_tokens = int(request.get("max_tokens", profile.token_limit))
        self.check_quota(scope, requested_tokens)
        candidates = (profile.default_model, *profile.fallback_models)
        bounded = min(max_attempts or (profile.retries + 1), len(candidates))
        if bounded <= 0:
            raise ValueError("At least one bounded attempt is required.")
        last_error: Exception | None = None
        for attempt, model_id in enumerate(candidates[:bounded]):
            model = self.get_model(model_id, scope)
            self.security.allowed(model.provider, model.id, scope)
            adapter = self.provider_adapters.get(model.provider)
            if adapter is None:
                last_error = RuntimeError(
                    f"Provider adapter unavailable: {model.provider}"
                )
                self.metrics.increment("model_failures_total")
                continue
            started = monotonic()
            try:
                response = adapter.invoke(model, dict(request))
                latency = monotonic() - started
                self.record_usage(
                    UsageRecord(
                        id=f"{profile_id}:{len(self.usage) + 1}",
                        model_id=model.id,
                        provider=model.provider,
                        tenant=scope.tenant,
                        workspace=scope.workspace,
                        input_tokens=int(response.get("input_tokens", 0)),
                        output_tokens=int(response.get("output_tokens", 0)),
                        latency_seconds=latency,
                        estimated_cost=float(response.get("estimated_cost", 0)),
                    ),
                    scope,
                )
                if attempt:
                    self.metrics.increment("model_fallback_total")
                return response
            except Exception as error:
                last_error = error
                self.metrics.increment("model_failures_total")
                kind = self.classify_failure(error)
                if kind in {
                    FailureKind.AUTHENTICATION,
                    FailureKind.INVALID_REQUEST,
                    FailureKind.POLICY,
                }:
                    break
        raise RuntimeError("All bounded model attempts failed.") from last_error

    def dashboard(self, scope: ModelScope) -> dict[str, Any]:
        self.security.authorize(scope, "models:read")
        models = self.list_models(scope)
        usage = [
            item
            for item in self.usage
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]
        return {
            "sections": DASHBOARD_SECTIONS,
            "models": len(models),
            "providers": len(self.providers),
            "profiles": len(
                [
                    item
                    for item in self.profiles.values()
                    if item.tenant == scope.tenant and item.workspace == scope.workspace
                ]
            ),
            "usage_records": len(usage),
            "cost": self.budget_status(scope),
            "metrics": self.metrics.snapshot(),
        }


__all__ = (
    "AccuracyEvaluator",
    "ActualUsage",
    "AuditEvent",
    "BenchmarkRecord",
    "Budget",
    "CostCalculator",
    "CustomProvider",
    "DASHBOARD_SECTIONS",
    "DeploymentKind",
    "EvaluationRecord",
    "FailureKind",
    "GovernanceRecord",
    "HealthStatus",
    "KubernetesDeployment",
    "LocalProvider",
    "METRICS",
    "ModelDeployment",
    "ModelMetrics",
    "ModelPlatform",
    "ModelProfile",
    "ModelRecord",
    "ModelScope",
    "ModelSecurity",
    "ModelStatus",
    "Provider",
    "ProviderConfiguration",
    "ProviderPricing",
    "Quota",
    "RouteRequest",
    "RoutingRule",
    "SafetyEvaluator",
    "ScalingConfiguration",
    "TRANSITIONS",
    "UsageRecord",
)
