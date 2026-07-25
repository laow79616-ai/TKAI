import pytest

from cloud.execution import ExecutionContext, ExecutionStatus, ReferenceExecutionService
from cloud.execution.errors import ExecutionLifecycleError


def test_reference_execution_is_declarative():
    service = ReferenceExecutionService()
    item = service.create("e", "d", "p", "w")
    assert item.status is ExecutionStatus.QUEUED
    assert (
        service.transition("e", ExecutionStatus.RUNNING).status
        is ExecutionStatus.RUNNING
    )
    with pytest.raises(ExecutionLifecycleError):
        service.transition("e", ExecutionStatus.ARCHIVED)
    service.close()
    service.close()
    assert service.list() == ()


def test_context_is_serializable():
    assert ExecutionContext(execution_id="e").to_dict()["execution_id"] == "e"
