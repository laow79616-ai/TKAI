"""Governed Enterprise AI Multi-Agent Intelligence control plane."""

from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import monotonic
from typing import Any

from .metrics import MultiAgentMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AgentStatus(str, Enum):
    DRAFT = "draft"
    PROVISIONED = "provisioned"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TeamRole(str, Enum):
    COORDINATOR = "coordinator"
    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    SUPERVISOR = "supervisor"
    OBSERVER = "observer"
    CUSTOM = "custom"


class ExecutionMode(str, Enum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    TIMED_OUT = "timed_out"


class DelegationStatus(str, Enum):
    ASSIGNED = "assigned"
    PENDING_APPROVAL = "pending_approval"
    ACCEPTED = "accepted"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class MultiAgentScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"multi_agent:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Agent:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    role: TeamRole
    capabilities: tuple[str, ...]
    status: AgentStatus = AgentStatus.DRAFT
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["role"] = self.role.value
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class AgentTeam:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    members: dict[str, TeamRole] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["members"] = {key: value.value for key, value in self.members.items()}
        return result


@dataclass(slots=True)
class AgentTask:
    id: str
    name: str
    description: str = ""
    priority: int = 0
    dependencies: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    resources: dict[str, float] = field(default_factory=dict)
    requires_approval: bool = False
    timeout_seconds: float = 0
    retry_limit: int = 0
    fallback_agent_id: str | None = None


@dataclass(slots=True)
class ExecutionPlan:
    id: str
    name: str
    goal: str
    tenant: str
    workspace: str
    owner: str
    tasks: list[AgentTask]
    milestones: tuple[str, ...] = ()
    risks: dict[str, float] = field(default_factory=dict)
    resource_allocation: dict[str, float] = field(default_factory=dict)
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Message:
    id: str
    tenant: str
    workspace: str
    sender_id: str
    body: dict[str, Any]
    recipient_id: str | None = None
    team_id: str | None = None
    event: str = "message"
    context_references: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["created_at"] = self.created_at.isoformat()
        return result


@dataclass(slots=True)
class Delegation:
    id: str
    task_id: str
    tenant: str
    workspace: str
    assigned_by: str
    assigned_to: str
    status: DelegationStatus = DelegationStatus.ASSIGNED
    approval_id: str | None = None
    escalation_target: str | None = None
    attempts: int = 0


@dataclass(slots=True)
class Vote:
    agent_id: str
    option: str
    confidence: float
    weight: float = 1
    approved: bool = True
    rationale: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1 or self.weight < 0:
            raise ValueError("Invalid confidence or weight.")


@dataclass(slots=True)
class ConsensusDecision:
    id: str
    tenant: str
    workspace: str
    topic: str
    votes: list[Vote]
    selected_option: str
    confidence: float
    approved: bool
    method: str
    review_required: bool


@dataclass(slots=True)
class Negotiation:
    id: str
    tenant: str
    workspace: str
    topic: str
    proposals: dict[str, dict[str, Any]]
    resolution: dict[str, Any]
    policy_compliant: bool
    status: str


@dataclass(slots=True)
class MemoryReference:
    id: str
    agent_id: str
    tenant: str
    workspace: str
    kind: str
    reference: str
    retention_policy: str = "session"
    private: bool = False


@dataclass(slots=True)
class KnowledgeReference:
    id: str
    tenant: str
    workspace: str
    reference: str
    kind: str = "knowledge_graph"
    query: str = ""
    evidence_references: tuple[str, ...] = ()
    score: float = 1


@dataclass(slots=True)
class ReasoningTrace:
    id: str
    tenant: str
    workspace: str
    agent_ids: tuple[str, ...]
    goal: str
    steps: list[dict[str, Any]]
    decision_trace_reference: str
    bounded: bool = True


@dataclass(slots=True)
class Execution:
    id: str
    plan_id: str
    tenant: str
    workspace: str
    mode: ExecutionMode
    status: ExecutionStatus = ExecutionStatus.QUEUED
    results: dict[str, Any] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["mode"] = self.mode.value
        result["status"] = self.status.value
        return result


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]


TaskHandler = Callable[[AgentTask, Mapping[str, Any]], Any]


class MultiAgentPlatform:
    """Secure reference implementation of multi-agent collaboration."""

    TRANSITIONS = {
        AgentStatus.DRAFT: {AgentStatus.PROVISIONED, AgentStatus.ARCHIVED},
        AgentStatus.PROVISIONED: {AgentStatus.READY, AgentStatus.ARCHIVED},
        AgentStatus.READY: {AgentStatus.RUNNING, AgentStatus.ARCHIVED},
        AgentStatus.RUNNING: {AgentStatus.PAUSED, AgentStatus.COMPLETED},
        AgentStatus.PAUSED: {
            AgentStatus.RUNNING,
            AgentStatus.COMPLETED,
            AgentStatus.ARCHIVED,
        },
        AgentStatus.COMPLETED: {AgentStatus.READY, AgentStatus.ARCHIVED},
        AgentStatus.ARCHIVED: {AgentStatus.DELETED},
        AgentStatus.DELETED: set(),
    }

    def __init__(self) -> None:
        self.agents: dict[str, Agent] = {}
        self.teams: dict[str, AgentTeam] = {}
        self.plans: dict[str, ExecutionPlan] = {}
        self.messages: list[Message] = []
        self.delegations: dict[str, Delegation] = {}
        self.consensus_decisions: list[ConsensusDecision] = []
        self.negotiations: list[Negotiation] = []
        self.memory_references: list[MemoryReference] = []
        self.knowledge_references: list[KnowledgeReference] = []
        self.reasoning_traces: list[ReasoningTrace] = []
        self.executions: list[Execution] = []
        self.audit: list[AuditEntry] = []
        self.safety_policies: dict[str, dict[str, Any]] = {}
        self.metrics = MultiAgentMetrics()
        self._handlers: dict[str, TaskHandler] = {}

    @staticmethod
    def _check(record: Any, scope: MultiAgentScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope multi-agent access denied.")

    @staticmethod
    def _require(scope: MultiAgentScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "multi_agent:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: MultiAgentScope, **metadata: Any) -> None:
        safe = {
            key: value
            for key, value in metadata.items()
            if not any(word in key.lower() for word in ("secret", "token", "password"))
        }
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), safe
            )
        )

    def create_agent(self, agent: Agent, scope: MultiAgentScope) -> Agent:
        self._require(scope, "multi_agent:write")
        self._check(agent, scope)
        if agent.id in self.agents or not agent.capabilities:
            raise ValueError("Agent must be unique and have capabilities.")
        self.agents[agent.id] = agent
        self.metrics.increment("multi_agents_total")
        self._audit("agent.create", scope, agent_id=agent.id)
        return agent

    def list_agents(self, scope: MultiAgentScope) -> list[Agent]:
        self._require(scope, "multi_agent:read")
        return [
            item
            for item in self.agents.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def set_agent_status(
        self, agent_id: str, status: AgentStatus, scope: MultiAgentScope
    ) -> Agent:
        self._require(scope, "multi_agent:write")
        agent = self.agents[agent_id]
        self._check(agent, scope)
        if status not in self.TRANSITIONS[agent.status]:
            raise ValueError(
                f"Invalid transition: {agent.status.value} -> {status.value}"
            )
        agent.status = status
        self._audit("agent.status", scope, agent_id=agent_id, status=status.value)
        return agent

    def create_team(self, team: AgentTeam, scope: MultiAgentScope) -> AgentTeam:
        self._require(scope, "multi_agent:write")
        self._check(team, scope)
        if not team.members or TeamRole.COORDINATOR not in team.members.values():
            raise ValueError("Team requires members and a coordinator.")
        for agent_id in team.members:
            self._check(self.agents[agent_id], scope)
        self.teams[team.id] = team
        self.metrics.increment("agent_teams_total")
        self._audit("team.create", scope, team_id=team.id)
        return team

    def send_message(self, message: Message, scope: MultiAgentScope) -> Message:
        self._require(scope, "multi_agent:communicate")
        self._check(message, scope)
        self._check(self.agents[message.sender_id], scope)
        if message.recipient_id:
            self._check(self.agents[message.recipient_id], scope)
        if message.team_id:
            self._check(self.teams[message.team_id], scope)
        if not message.recipient_id and not message.team_id:
            raise ValueError("A direct, team, or broadcast destination is required.")
        self.messages.append(message)
        self._audit("communication.message", scope, message_id=message.id)
        return message

    def create_plan(self, plan: ExecutionPlan, scope: MultiAgentScope) -> ExecutionPlan:
        self._require(scope, "multi_agent:plan")
        self._check(plan, scope)
        ids = {item.id for item in plan.tasks}
        if len(ids) != len(plan.tasks) or any(
            not set(item.dependencies).issubset(ids) for item in plan.tasks
        ):
            raise ValueError("Tasks must be unique and dependencies must exist.")
        self._ordered(plan.tasks)
        if any(not 0 <= risk <= 1 for risk in plan.risks.values()):
            raise ValueError("Risk must be within [0, 1].")
        plan.status = "ready"
        self.plans[plan.id] = plan
        self._audit("planning.create", scope, plan_id=plan.id)
        return plan

    @staticmethod
    def _ordered(tasks: list[AgentTask]) -> list[AgentTask]:
        pending = {item.id: item for item in tasks}
        complete: set[str] = set()
        ordered: list[AgentTask] = []
        while pending:
            ready = sorted(
                (
                    item
                    for item in pending.values()
                    if set(item.dependencies).issubset(complete)
                ),
                key=lambda item: (-item.priority, item.id),
            )
            if not ready:
                raise ValueError("Cyclic task dependencies are not allowed.")
            for item in ready:
                ordered.append(item)
                complete.add(item.id)
                pending.pop(item.id)
        return ordered

    def coordinate(
        self, team_id: str, plan_id: str, scope: MultiAgentScope
    ) -> dict[str, str]:
        self._require(scope, "multi_agent:coordinate")
        team, plan = self.teams[team_id], self.plans[plan_id]
        self._check(team, scope)
        self._check(plan, scope)
        assignments: dict[str, str] = {}
        loads = dict.fromkeys(team.members, 0)
        for task in self._ordered(plan.tasks):
            candidates = [
                self.agents[agent_id]
                for agent_id, role in team.members.items()
                if role in {TeamRole.EXECUTOR, TeamRole.PLANNER, TeamRole.CUSTOM}
                and set(task.required_capabilities).issubset(
                    self.agents[agent_id].capabilities
                )
                and self.agents[agent_id].status
                in {AgentStatus.READY, AgentStatus.RUNNING}
            ]
            if not candidates:
                self.metrics.increment("multi_agent_failures_total")
                raise RuntimeError(f"No eligible agent for task {task.id}.")
            selected = min(candidates, key=lambda item: (loads[item.id], item.id))
            assignments[task.id] = selected.id
            loads[selected.id] += 1
        self.metrics.increment("coordination_cycles_total")
        self._audit("coordination.cycle", scope, assignments=assignments)
        return assignments

    def delegate(
        self,
        task_id: str,
        assigned_to: str,
        scope: MultiAgentScope,
        requires_approval: bool = False,
        escalation_target: str | None = None,
    ) -> Delegation:
        self._require(scope, "multi_agent:delegate")
        self._check(self.agents[assigned_to], scope)
        item = Delegation(
            secrets.token_hex(12),
            task_id,
            scope.tenant,
            scope.workspace,
            scope.actor,
            assigned_to,
            DelegationStatus.PENDING_APPROVAL
            if requires_approval
            else DelegationStatus.ASSIGNED,
            secrets.token_hex(12) if requires_approval else None,
            escalation_target,
        )
        self.delegations[item.id] = item
        self.metrics.increment("delegations_total")
        self._audit("delegation.assign", scope, delegation_id=item.id)
        return item

    def approve_delegation(
        self, delegation_id: str, approved: bool, scope: MultiAgentScope
    ) -> Delegation:
        self._require(scope, "multi_agent:approve")
        item = self.delegations[delegation_id]
        self._check(item, scope)
        item.status = (
            DelegationStatus.ACCEPTED if approved else DelegationStatus.ESCALATED
        )
        self._audit("delegation.approval", scope, delegation_id=item.id)
        return item

    def build_consensus(
        self,
        topic: str,
        votes: list[Vote],
        scope: MultiAgentScope,
        method: str = "majority",
    ) -> ConsensusDecision:
        self._require(scope, "multi_agent:consensus")
        if method not in {"majority", "weighted"} or not votes:
            raise ValueError("Consensus requires votes and a supported method.")
        totals: dict[str, float] = {}
        for vote in votes:
            self._check(self.agents[vote.agent_id], scope)
            value = vote.weight * vote.confidence if method == "weighted" else 1
            totals[vote.option] = totals.get(vote.option, 0) + value
        selected = max(sorted(totals), key=totals.__getitem__)
        confidence = totals[selected] / sum(totals.values())
        approved = sum(vote.approved for vote in votes) > len(votes) / 2
        decision = ConsensusDecision(
            secrets.token_hex(12),
            scope.tenant,
            scope.workspace,
            topic,
            votes,
            selected,
            confidence,
            approved,
            method,
            confidence < 0.7,
        )
        self.consensus_decisions.append(decision)
        self.metrics.increment("consensus_total")
        self._audit("consensus.decide", scope, decision_id=decision.id)
        return decision

    def negotiate(
        self,
        topic: str,
        proposals: dict[str, dict[str, Any]],
        scope: MultiAgentScope,
        policy: Mapping[str, Any] | None = None,
    ) -> Negotiation:
        self._require(scope, "multi_agent:negotiate")
        maximum = float((policy or {}).get("maximum_resource", float("inf")))
        compliant = all(
            float(value.get("resource", 0)) <= maximum for value in proposals.values()
        )
        ranked = sorted(
            proposals.items(),
            key=lambda item: (
                -int(item[1].get("priority", 0)),
                float(item[1].get("resource", 0)),
            ),
        )
        if not ranked:
            raise ValueError("Negotiation requires proposals.")
        winner, proposal = ranked[0]
        item = Negotiation(
            secrets.token_hex(12),
            scope.tenant,
            scope.workspace,
            topic,
            proposals,
            {"agent_id": winner, "proposal": proposal},
            compliant,
            "resolved" if compliant else "policy_review",
        )
        self.negotiations.append(item)
        return item

    def add_memory_reference(
        self, item: MemoryReference, scope: MultiAgentScope
    ) -> MemoryReference:
        self._require(scope, "multi_agent:write")
        self._check(item, scope)
        if item.kind not in {"shared", "private", "session", "knowledge"}:
            raise ValueError("Unsupported memory kind.")
        self.memory_references.append(item)
        return item

    def add_knowledge_reference(
        self, item: KnowledgeReference, scope: MultiAgentScope
    ) -> KnowledgeReference:
        self._require(scope, "multi_agent:write")
        self._check(item, scope)
        if not 0 <= item.score <= 1:
            raise ValueError("Knowledge score must be within [0, 1].")
        self.knowledge_references.append(item)
        return item

    def semantic_search(
        self, query: str, scope: MultiAgentScope
    ) -> list[KnowledgeReference]:
        self._require(scope, "multi_agent:read")
        terms = set(query.lower().split())
        return sorted(
            (
                item
                for item in self.knowledge_references
                if item.tenant == scope.tenant
                and item.workspace == scope.workspace
                and terms.intersection(f"{item.query} {item.reference}".lower().split())
            ),
            key=lambda item: -item.score,
        )

    def record_reasoning(
        self, item: ReasoningTrace, scope: MultiAgentScope
    ) -> ReasoningTrace:
        self._require(scope, "multi_agent:reason")
        self._check(item, scope)
        if not item.bounded or len(item.steps) > 100:
            raise ValueError("Reasoning must use the bounded interface.")
        self.reasoning_traces.append(item)
        return item

    def register_handler(self, task_name: str, handler: TaskHandler) -> None:
        self._handlers[task_name] = handler

    def execute_plan(
        self,
        plan_id: str,
        scope: MultiAgentScope,
        mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
        context: Mapping[str, Any] | None = None,
    ) -> Execution:
        self._require(scope, "multi_agent:execute")
        plan = self.plans[plan_id]
        self._check(plan, scope)
        item = Execution(
            secrets.token_hex(12), plan.id, scope.tenant, scope.workspace, mode
        )
        self.executions.append(item)
        item.status, plan.status = ExecutionStatus.RUNNING, "running"
        started = monotonic()
        try:
            for task in self._ordered(plan.tasks):
                attempts = 0
                while True:
                    attempts += 1
                    try:
                        handler = self._handlers.get(
                            task.name, lambda current, payload: {"accepted": current.id}
                        )
                        item.results[task.id] = handler(task, context or {})
                        item.checkpoints.append(dict(item.results))
                        break
                    except Exception:
                        if attempts > task.retry_limit:
                            raise
            item.status, plan.status = ExecutionStatus.SUCCEEDED, "completed"
        except Exception as error:
            item.failures.append(str(error))
            item.status = (
                ExecutionStatus.ROLLED_BACK
                if item.checkpoints
                else ExecutionStatus.FAILED
            )
            plan.status = "paused"
            self.metrics.increment("multi_agent_failures_total")
        finally:
            item.duration_seconds = monotonic() - started
            self.metrics.increment("multi_agent_latency_seconds", item.duration_seconds)
            self._audit("execution.complete", scope, status=item.status.value)
        return item

    def health(self, scope: MultiAgentScope) -> dict[str, Any]:
        agents = self.list_agents(scope)
        executions = [
            item
            for item in self.executions
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]
        successes = sum(item.status is ExecutionStatus.SUCCEEDED for item in executions)
        return {
            "status": "healthy" if successes == len(executions) else "degraded",
            "agents": len(agents),
            "latency": sum(item.duration_seconds for item in executions),
            "utilization": (
                sum(item.status is AgentStatus.RUNNING for item in agents) / len(agents)
                if agents
                else 0
            ),
            "success_rate": successes / len(executions) if executions else 1,
            "failures": len(executions) - successes,
        }

    def configure_governance(
        self, policy_id: str, policy: dict[str, Any], scope: MultiAgentScope
    ) -> dict[str, Any]:
        self._require(scope, "multi_agent:admin")
        if {"secret", "password", "token", "api_key"}.intersection(
            key.lower() for key in policy
        ):
            raise ValueError("Policies may contain references, not secrets.")
        self.safety_policies[policy_id] = dict(policy)
        self._audit("governance.configure", scope, policy_id=policy_id)
        return self.safety_policies[policy_id]

    def dashboard(self, scope: MultiAgentScope) -> dict[str, Any]:
        scoped = lambda item: (  # noqa: E731
            item.tenant == scope.tenant and item.workspace == scope.workspace
        )
        return {
            "agents": [item.to_dict() for item in self.list_agents(scope)],
            "teams": [item.to_dict() for item in self.teams.values() if scoped(item)],
            "coordination": self.metrics.snapshot()["coordination_cycles_total"],
            "execution": [item.to_dict() for item in self.executions if scoped(item)],
            "planning": [
                item.to_dict() for item in self.plans.values() if scoped(item)
            ],
            "consensus": [
                asdict(item) for item in self.consensus_decisions if scoped(item)
            ],
            "negotiation": [asdict(item) for item in self.negotiations if scoped(item)],
            "memory": [asdict(item) for item in self.memory_references if scoped(item)],
            "knowledge": [
                asdict(item) for item in self.knowledge_references if scoped(item)
            ],
            "health": self.health(scope),
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAIMultiAgentIntelligencePlatform = MultiAgentPlatform

__all__ = (
    "Agent",
    "AgentStatus",
    "AgentTask",
    "AgentTeam",
    "AuditEntry",
    "ConsensusDecision",
    "Delegation",
    "DelegationStatus",
    "EnterpriseAIMultiAgentIntelligencePlatform",
    "Execution",
    "ExecutionMode",
    "ExecutionPlan",
    "ExecutionStatus",
    "KnowledgeReference",
    "MemoryReference",
    "Message",
    "MultiAgentPlatform",
    "MultiAgentScope",
    "Negotiation",
    "ReasoningTrace",
    "TaskHandler",
    "TeamRole",
    "Vote",
)
