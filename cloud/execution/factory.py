from .lifecycle import ExecutionStatus
from .models import ExecutionDescriptor


class ExecutionFactory:
    def create(self, execution_id, deployment_id, project_id, workspace_id):
        return ExecutionDescriptor(
            execution_id,
            deployment_id,
            project_id,
            workspace_id,
            ExecutionStatus.QUEUED,
        )
