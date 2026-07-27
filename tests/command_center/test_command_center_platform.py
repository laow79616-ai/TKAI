import pytest

from command_center import (
    ActivityType,
    Alert,
    AlertSeverity,
    AlertStatus,
    CommandCenter,
    CommandCenterPlatform,
    CommandCenterScope,
    CommandCenterStatus,
    ControlPlane,
    ControlPlaneLevel,
    ExecutionStatus,
    HealthSnapshot,
    Incident,
    IncidentPriority,
    Operation,
    Playbook,
    Task,
    TaskType,
    TopologyNode,
    Visibility,
)


@pytest.fixture
def system() -> tuple[CommandCenterPlatform, CommandCenterScope]:
    platform = CommandCenterPlatform()
    scope = CommandCenterScope(
        "tenant-a",
        "workspace-a",
        "operator",
        frozenset({"command_center:admin"}),
    )
    platform.create_command_center(
        CommandCenter(
            "cc-1",
            "Enterprise Command",
            "Unified enterprise operations",
            scope.tenant,
            scope.workspace,
            scope.actor,
            visibility=Visibility.WORKSPACE,
        ),
        scope,
    )
    return platform, scope


def test_lifecycle_approval_and_isolation(
    system: tuple[CommandCenterPlatform, CommandCenterScope],
) -> None:
    platform, scope = system
    assert (
        platform.set_status("cc-1", CommandCenterStatus.ACTIVE, scope).status
        is CommandCenterStatus.ACTIVE
    )
    assert (
        platform.set_status("cc-1", CommandCenterStatus.MAINTENANCE, scope).status
        is CommandCenterStatus.MAINTENANCE
    )
    assert (
        platform.set_status("cc-1", CommandCenterStatus.PAUSED, scope).status
        is CommandCenterStatus.PAUSED
    )
    with pytest.raises(PermissionError, match="Approval"):
        platform.set_status("cc-1", CommandCenterStatus.ARCHIVED, scope)
    platform.set_status("cc-1", CommandCenterStatus.ARCHIVED, scope, "approval-1")
    platform.set_status("cc-1", CommandCenterStatus.DELETED, scope, "approval-2")
    other = CommandCenterScope("tenant-b", "workspace-a", "attacker")
    assert platform.resource("overview", other)["instances"] == 0


def test_control_plane_operations_alerts_and_incidents(
    system: tuple[CommandCenterPlatform, CommandCenterScope],
) -> None:
    platform, scope = system
    plane = platform.add_control_plane(
        ControlPlane(
            "plane-1",
            scope.tenant,
            scope.workspace,
            "Tenant plane",
            ControlPlaneLevel.TENANT,
        ),
        scope,
    )
    assert (
        platform.synchronize_control_plane(plane.id, scope, "healthy").synchronization
        == "synchronized"
    )
    operation = platform.add_operation(
        Operation(
            "op-1",
            scope.tenant,
            scope.workspace,
            "Agent rollout",
            "deployment",
            resource_usage={"cpu": 0.4},
            capacity={"cpu": 1.0},
        ),
        scope,
    )
    platform.set_operation_status(operation.id, ExecutionStatus.RUNNING, scope)
    alert = platform.add_alert(
        Alert(
            "alert-1",
            scope.tenant,
            scope.workspace,
            AlertSeverity.CRITICAL,
            "availability",
            "gateway",
            "error-rate",
        ),
        scope,
    )
    platform.update_alert(alert.id, AlertStatus.ACKNOWLEDGED, scope, "investigating")
    platform.update_alert(alert.id, AlertStatus.ESCALATED, scope, "on-call")
    platform.update_alert(alert.id, AlertStatus.RESOLVED, scope, "recovered")
    incident = platform.add_incident(
        Incident(
            "incident-1",
            scope.tenant,
            scope.workspace,
            "Gateway errors",
            IncidentPriority.P1,
            "Customer traffic degraded",
            scope.actor,
        ),
        scope,
    )
    platform.resolve_incident(
        incident.id,
        scope,
        "Rolled back",
        "Traffic healthy",
        "rca://incident-1",
        "postmortem://incident-1",
    )
    dashboard = platform.dashboard(scope)
    assert dashboard["operations"]["jobs"]["running"] == 1
    assert dashboard["alerts"][0]["status"] == "resolved"
    assert dashboard["incidents"][0]["root_cause_reference"]
    assert platform.metrics.snapshot()["active_alerts_total"] == 0


def test_tasks_playbooks_topology_health_activity_and_security(
    system: tuple[CommandCenterPlatform, CommandCenterScope],
) -> None:
    platform, scope = system
    base = platform.add_task(
        Task(
            "task-1",
            scope.tenant,
            scope.workspace,
            "Drain service",
            TaskType.MANUAL,
        ),
        scope,
    )
    base.execution_status = ExecutionStatus.COMPLETED
    task = platform.add_task(
        Task(
            "task-2",
            scope.tenant,
            scope.workspace,
            "Rollback",
            TaskType.AUTOMATED,
            dependencies=("task-1",),
            retry_limit=1,
        ),
        scope,
    )
    assert (
        platform.execute_task(task.id, scope).execution_status
        is ExecutionStatus.RUNNING
    )
    playbook = platform.add_playbook(
        Playbook(
            "playbook-1",
            scope.tenant,
            scope.workspace,
            "Gateway recovery",
            ("Acknowledge alert", "Drain service", "Rollback"),
            "workflow://rollback",
            ("Restore prior release",),
            ("change-manager",),
        ),
        scope,
    )
    with pytest.raises(PermissionError, match="approvals"):
        platform.execute_playbook(playbook.id, scope)
    platform.execute_playbook(playbook.id, scope, ("change-manager",))
    service = platform.add_topology_node(
        TopologyNode(
            "service-1",
            scope.tenant,
            scope.workspace,
            "Gateway",
            "service",
            health="healthy",
        ),
        scope,
    )
    platform.add_topology_node(
        TopologyNode(
            "agent-1",
            scope.tenant,
            scope.workspace,
            "Recovery agent",
            "agent",
            (service.id,),
            "healthy",
        ),
        scope,
    )
    platform.record_health(
        HealthSnapshot(
            "health-1",
            scope.tenant,
            scope.workspace,
            service.id,
            0.999,
            0.08,
            0.001,
            0.8,
            0.5,
            prediction_reference="prediction://gateway",
        ),
        scope,
    )
    assert len(platform.topology(scope)["edges"]) == 1
    assert platform.dashboard(scope)["agents"][0]["id"] == "agent-1"
    assert platform.activity_feed(
        scope, query="playbook", event_type=ActivityType.AUTOMATION
    )
    with pytest.raises(ValueError, match="Secrets"):
        platform.create_command_center(
            CommandCenter(
                "unsafe",
                "Unsafe",
                "",
                scope.tenant,
                scope.workspace,
                scope.actor,
                metadata={"api_token": "plaintext"},
            ),
            scope,
        )
    assert "plaintext" not in str(platform.activity_feed(scope))
