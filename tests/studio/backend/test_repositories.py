"""Reference repository CRUD and deterministic filtering tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from studio.backend.errors import StudioConflictError, StudioNotFoundError
from studio.backend.repositories import (
    InMemoryExecutionRepository,
    InMemoryProjectRepository,
    InMemoryWorkflowRepository,
)
from studio.shared import (
    ExecutionRecord,
    ExecutionStatus,
    StudioProject,
    StudioWorkflow,
)


def test_reference_repositories_support_crud_filtering_and_stable_errors() -> None:
    """Repositories are local, deterministic, and preserve immutable model snapshots."""
    projects = InMemoryProjectRepository()
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    project = projects.create(StudioProject("p1", "Project"))
    workflow = workflows.create(StudioWorkflow("w1", project.project_id, "Workflow"))
    execution = executions.create(
        ExecutionRecord(
            "e1", workflow.workflow_id, ExecutionStatus.PENDING, project_id="p1"
        )
    )

    assert workflows.list(project_id="p1") == (workflow,)
    assert executions.list(workflow_id="w1") == (execution,)
    assert (
        executions.update_status("e1", ExecutionStatus.SUCCEEDED).status
        is ExecutionStatus.SUCCEEDED
    )
    with pytest.raises(StudioConflictError):
        projects.create(project)
    projects.delete("p1")
    with pytest.raises(StudioNotFoundError):
        projects.get("p1")


def test_project_repository_handles_bounded_concurrent_reference_writes() -> None:
    """A local lock protects deterministic concurrent project creation."""
    repository = InMemoryProjectRepository()
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: repository.create(StudioProject(f"p-{index}", "Project")),
                range(16),
            )
        )
    assert len(repository.list()) == 16
