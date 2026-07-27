import pytest

from multi_agent import (
    Agent,
    AgentStatus,
    AgentTask,
    AgentTeam,
    ExecutionMode,
    ExecutionPlan,
    ExecutionStatus,
    KnowledgeReference,
    MemoryReference,
    Message,
    MultiAgentPlatform,
    MultiAgentScope,
    ReasoningTrace,
    TeamRole,
    Vote,
)


@pytest.fixture
def system():
    platform = MultiAgentPlatform()
    permissions = frozenset(
        {
            "multi_agent:read",
            "multi_agent:write",
            "multi_agent:plan",
            "multi_agent:coordinate",
            "multi_agent:communicate",
            "multi_agent:delegate",
            "multi_agent:approve",
            "multi_agent:consensus",
            "multi_agent:negotiate",
            "multi_agent:reason",
            "multi_agent:execute",
        }
    )
    scope = MultiAgentScope("tenant", "workspace", "owner", permissions)
    agents = [
        Agent(
            "coordinator",
            "Coordinator",
            "Coordinates",
            "tenant",
            "workspace",
            "owner",
            TeamRole.COORDINATOR,
            ("planning",),
        ),
        Agent(
            "executor",
            "Executor",
            "Executes",
            "tenant",
            "workspace",
            "owner",
            TeamRole.EXECUTOR,
            ("python",),
        ),
    ]
    for agent in agents:
        platform.create_agent(agent, scope)
        platform.set_agent_status(agent.id, AgentStatus.PROVISIONED, scope)
        platform.set_agent_status(agent.id, AgentStatus.READY, scope)
    team = AgentTeam(
        "team",
        "Delivery",
        "Enterprise team",
        "tenant",
        "workspace",
        "owner",
        {"coordinator": TeamRole.COORDINATOR, "executor": TeamRole.EXECUTOR},
    )
    platform.create_team(team, scope)
    return platform, scope


def test_lifecycle_team_coordination_and_planning(system):
    platform, scope = system
    plan = ExecutionPlan(
        "plan",
        "Launch",
        "Deliver safely",
        "tenant",
        "workspace",
        "owner",
        [
            AgentTask("build", "build", required_capabilities=("python",)),
            AgentTask("verify", "verify", dependencies=("build",), priority=10),
        ],
        ("release",),
        {"delivery": 0.2},
        {"cpu": 2},
    )
    platform.create_plan(plan, scope)
    assert platform.coordinate("team", "plan", scope) == {
        "build": "executor",
        "verify": "executor",
    }
    assert platform.metrics.snapshot()["coordination_cycles_total"] == 1
    with pytest.raises(ValueError):
        platform.set_agent_status("executor", AgentStatus.DELETED, scope)


def test_communication_delegation_consensus_and_negotiation(system):
    platform, scope = system
    platform.send_message(
        Message(
            "message",
            "tenant",
            "workspace",
            "coordinator",
            {"task": "build"},
            recipient_id="executor",
            context_references=("context://release",),
        ),
        scope,
    )
    delegation = platform.delegate("build", "executor", scope, True, "coordinator")
    assert (
        platform.approve_delegation(delegation.id, True, scope).status.value
        == "accepted"
    )
    decision = platform.build_consensus(
        "release",
        [Vote("coordinator", "go", 0.9), Vote("executor", "go", 0.8)],
        scope,
        "weighted",
    )
    assert decision.approved and decision.selected_option == "go"
    negotiation = platform.negotiate(
        "capacity",
        {"executor": {"priority": 10, "resource": 2}},
        scope,
        {"maximum_resource": 4},
    )
    assert negotiation.policy_compliant


def test_memory_knowledge_reasoning_execution_monitoring_dashboard(system):
    platform, scope = system
    platform.add_memory_reference(
        MemoryReference(
            "memory", "executor", "tenant", "workspace", "shared", "memory://1"
        ),
        scope,
    )
    platform.add_knowledge_reference(
        KnowledgeReference(
            "knowledge",
            "tenant",
            "workspace",
            "graph://release",
            query="release evidence",
            evidence_references=("evidence://1",),
        ),
        scope,
    )
    assert platform.semantic_search("release", scope)
    platform.record_reasoning(
        ReasoningTrace(
            "trace",
            "tenant",
            "workspace",
            ("coordinator", "executor"),
            "release",
            [{"decision": "go"}],
            "trace://decision",
        ),
        scope,
    )
    platform.create_plan(
        ExecutionPlan(
            "execute",
            "Execute",
            "Run",
            "tenant",
            "workspace",
            "owner",
            [AgentTask("work", "work")],
        ),
        scope,
    )
    execution = platform.execute_plan("execute", scope, ExecutionMode.PARALLEL)
    assert execution.status is ExecutionStatus.SUCCEEDED
    assert platform.health(scope)["success_rate"] == 1
    assert {
        "agents",
        "teams",
        "coordination",
        "execution",
        "planning",
        "consensus",
        "negotiation",
        "memory",
        "knowledge",
        "health",
    } <= platform.dashboard(scope).keys()


def test_isolation_rbac_governance_recovery_and_audit(system):
    platform, scope = system
    foreign = MultiAgentScope("other", "workspace", "intruder")
    assert platform.list_agents(foreign) == []
    with pytest.raises(PermissionError):
        platform.set_agent_status("executor", AgentStatus.RUNNING, foreign)
    admin = MultiAgentScope(
        "tenant", "workspace", "admin", frozenset({"multi_agent:admin"})
    )
    assert platform.configure_governance("safe", {"approval_required": True}, admin)[
        "approval_required"
    ]
    with pytest.raises(ValueError):
        platform.configure_governance("bad", {"token": "raw"}, admin)
    assert "raw" not in str(platform.audit)
