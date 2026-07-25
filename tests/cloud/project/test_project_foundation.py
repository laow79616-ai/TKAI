"""Offline Cloud Project Foundation tests with no network or environment access."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from cloud import Project, ProjectStatus
from cloud.project import (
    ProjectContext,
    ProjectDescriptor,
    ProjectGraph,
    ProjectMembershipDescriptor,
    ProjectValidation,
    ReferenceProjectService,
    WorkspaceProjectBinding,
)
from cloud.project.errors import ProjectConflictError, ProjectNotFoundError
from cloud.project.policy import ProjectPolicy


class AcceptingProjectPolicy:
    """Local test policy that only reports declarative validation results."""

    def validate_creation(self, project: Project) -> ProjectValidation:
        return ProjectValidation(True)

    def validate_update(self, project: Project) -> ProjectValidation:
        return ProjectValidation(True, warnings=("reference",))

    def validate_context(self, context: ProjectContext) -> ProjectValidation:
        return ProjectValidation(context.project_id is not None)

    def validate_binding(self, binding: WorkspaceProjectBinding) -> ProjectValidation:
        return ProjectValidation(True)


def test_project_model_is_immutable_json_safe_and_uses_utc_timestamps() -> None:
    """Project keeps all architecture fields without credential-bearing state."""
    source = {"scope": "reference"}
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    project = Project(
        "project-1",
        "workspace-1",
        "My Project",
        metadata=source,
        tags={"cloud", "reference"},
        created_at=now,
        updated_at=now,
    )
    source["scope"] = "changed"

    assert project.slug == "my-project"
    assert project.status is ProjectStatus.ACTIVE
    assert project.to_dict()["tags"] == ["cloud", "reference"]
    assert project.to_dict()["created_at"].endswith("+00:00")
    assert project.to_dict()["metadata"] == {"scope": "reference"}
    with pytest.raises(FrozenInstanceError):
        project.name = "other"  # type: ignore[misc]


def test_project_context_and_descriptor_are_explicit_defensive_snapshots() -> None:
    """Context and descriptor never infer account scope or mutate caller input."""
    source = {"kind": "test"}
    context = ProjectContext("project-1", "workspace-1", metadata=source)
    descriptor = ProjectDescriptor(
        "project-1", capabilities={"reference"}, metadata=source
    )
    source["kind"] = "changed"

    assert context.to_dict()["metadata"] == {"kind": "test"}
    assert dict(descriptor.metadata) == {"kind": "test"}


def test_reference_service_registers_projects_and_workspace_bindings() -> None:
    """One workspace may own many declared projects without permission inheritance."""
    service = ReferenceProjectService()
    service.create("project-b", "workspace-1", "B")
    service.create("project-a", "workspace-1", "A")
    service.create("project-c", "workspace-2", "C")

    assert [project.project_id for project in service.projects("workspace-1")] == [
        "project-a",
        "project-b",
    ]
    assert service.registry.binding("project-a") == WorkspaceProjectBinding(
        "workspace-1", "project-a"
    )


def test_project_membership_is_project_local_and_graph_is_stable() -> None:
    """Workspace membership is not copied into a project membership declaration."""
    service = ReferenceProjectService()
    project = service.create("project-1", "workspace-1", "Project")
    service.add_membership(ProjectMembershipDescriptor("project-1", "principal-b"))
    service.add_membership(ProjectMembershipDescriptor("project-1", "principal-a"))

    graph = ProjectGraph.snapshot(
        project,
        service.registry.binding("project-1"),
        service.memberships("project-1"),
    )

    assert graph.to_dict() == {
        "nodes": ["workspace-1", "project-1", "principal-a", "principal-b"],
        "edges": [
            ["workspace-1", "project-1"],
            ["project-1", "principal-a"],
            ["project-1", "principal-b"],
        ],
    }


def test_registry_snapshot_conflicts_and_cleanup_are_explicit() -> None:
    """Reference registry operations expose only local, stable state."""
    service = ReferenceProjectService()
    service.create("project-1", "workspace-1", "Project")

    assert service.registry.snapshot() == (service.project("project-1"),)
    with pytest.raises(ProjectConflictError):
        service.create("project-1", "workspace-1", "Duplicate")
    with pytest.raises(ProjectNotFoundError):
        service.project("missing")
    service.close()
    service.close()
    assert service.projects() == ()


def test_project_policy_contract_has_declarative_results_only() -> None:
    """Policy validation reports results and does not execute a project action."""
    policy: ProjectPolicy = AcceptingProjectPolicy()
    project = Project("project-1", "workspace-1", "Project")

    assert policy.validate_creation(project).valid
    assert policy.validate_update(project).warnings == ("reference",)
    assert policy.validate_context(ProjectContext()).valid is False
    binding = WorkspaceProjectBinding("workspace-1", "project-1")
    assert policy.validate_binding(binding).valid


def test_reference_project_registry_is_safe_for_bounded_concurrent_writes() -> None:
    """Local registry locking preserves all independently created project ids."""
    service = ReferenceProjectService()

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: service.create(
                    f"project-{index}", "workspace-1", f"Project {index}"
                ),
                range(8),
            )
        )

    assert len(service.projects("workspace-1")) == 8
