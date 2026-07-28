"""Domain contracts for the Enterprise TikTok AI Execution Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    QUEUED = "queued"
    DISPATCHING = "dispatching"
    RUNNING = "running"
    PAUSED = "paused"
    CHECKPOINTED = "checkpointed"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    ARCHIVED = "archived"
    DELETED = "deleted"


class StageKind(str, Enum):
    VALIDATION = "validation"
    PREPARATION = "preparation"
    RESOURCE_ALLOCATION = "resource_allocation"
    DISPATCH = "dispatch"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    COMPLETION = "completion"
    CLEANUP = "cleanup"


class PipelineKind(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    CHECKPOINTED = "checkpointed"
    RETRYABLE = "retryable"
    RECOVERABLE = "recoverable"


class VerificationKind(str, Enum):
    APPROVAL = "approval_validation"
    RISK = "risk_validation"
    RESOURCE = "resource_validation"
    RUNTIME = "runtime_validation"
    DEPENDENCY = "dependency_validation"
    WORKSPACE = "workspace_validation"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


INTEGRATION_MODULES = (
    "operations_planner",
    "automation_engine",
    "runtime_manager",
    "resource_center",
    "task_scheduler",
    "browser_cluster",
    "device_center",
    "account_center",
    "proxy_center",
    "workflow_center",
    "risk_control",
)

FORBIDDEN_TERMS = (
    "captcha",
    "bypass",
    "circumvent",
    "anti-detection",
    "spam",
    "mass_action",
    "unrestricted",
)


def validate_safe_mapping(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in execution metadata.")


@dataclass(frozen=True, slots=True)
class ExecutionScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:execution:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class ExecutionStep:
    id: str
    name: str
    module: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    condition: str = ""
    maximum_attempts: int = 1
    checkpoint_after: bool = False
    rollback_action: str = ""

    def validate(self) -> None:
        if not all((self.id, self.name, self.module, self.action)):
            raise ValueError("Step identity, module, and action are required.")
        if self.module not in INTEGRATION_MODULES:
            raise ValueError("Step module is outside the bounded integration set.")
        if not 1 <= self.maximum_attempts <= 3:
            raise ValueError("Step attempts must be within [1, 3].")
        text = f"{self.action} {self.rollback_action}".casefold()
        if any(term in text for term in FORBIDDEN_TERMS):
            raise ValueError("Unsafe or unrestricted execution action is forbidden.")
        validate_safe_mapping(self.payload)


@dataclass(slots=True)
class ExecutionPipeline:
    id: str
    execution_id: str
    tenant: str
    workspace: str
    kind: PipelineKind
    steps: list[ExecutionStep]
    maximum_concurrency: int = 1
    continue_on_failure: bool = False

    def validate(self) -> None:
        if not self.steps or len(self.steps) > 100:
            raise ValueError("Pipelines require between 1 and 100 bounded steps.")
        if not 1 <= self.maximum_concurrency <= 10:
            raise ValueError("Pipeline concurrency must be within [1, 10].")
        if self.kind is not PipelineKind.PARALLEL and self.maximum_concurrency != 1:
            raise ValueError("Only parallel pipelines may use concurrency.")
        ids = {step.id for step in self.steps}
        if len(ids) != len(self.steps):
            raise ValueError("Pipeline step IDs must be unique.")
        for step in self.steps:
            step.validate()
            if set(step.depends_on) - ids or step.id in step.depends_on:
                raise ValueError(
                    "Step dependencies must reference other pipeline steps."
                )


@dataclass(slots=True)
class ExecutionPlan:
    id: str
    name: str
    tenant: str
    workspace: str
    owner: str
    approved_plan_reference: str
    workflow_reference: str
    automation_reference: str
    runtime_reference: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def validate(self) -> None:
        identity = (
            self.id,
            self.name,
            self.tenant,
            self.workspace,
            self.owner,
            self.approved_plan_reference,
            self.workflow_reference,
            self.automation_reference,
            self.runtime_reference,
        )
        if not all(identity):
            raise ValueError("Execution identity, scope, and references are required.")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class ExecutionStage:
    id: str
    execution_id: str
    tenant: str
    workspace: str
    kind: StageKind
    status: StageStatus = StageStatus.PENDING
    progress: float = 0
    detail: str = ""


@dataclass(slots=True)
class VerificationRecord:
    id: str
    execution_id: str
    tenant: str
    workspace: str
    kind: VerificationKind
    passed: bool
    detail: str
    checked_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Checkpoint:
    id: str
    execution_id: str
    tenant: str
    workspace: str
    completed_step_ids: list[str]
    resource_references: list[str]
    runtime_reference: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class StepResult:
    id: str
    execution_id: str
    step_id: str
    tenant: str
    workspace: str
    success: bool
    output_reference: str
    attempts: int
    latency_seconds: float
    error: str = ""


@dataclass(slots=True)
class AuditEvent:
    execution_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    detail: str
    timestamp: datetime = field(default_factory=utcnow)
