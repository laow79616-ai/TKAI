"""Dashboard navigation and summary projection."""

from workflow_platform.models import Scope
from workflow_platform.service import WorkflowPlatform

SECTIONS = (
    "Workflow List",
    "Designer",
    "Executions",
    "History",
    "Templates",
    "Approvals",
    "Forms",
)


def dashboard(platform: WorkflowPlatform, scope: Scope) -> dict[str, object]:
    return {
        "sections": SECTIONS,
        "workflows": [item.to_dict() for item in platform.list(scope)],
        "executions": [item.to_dict() for item in platform.history.list(scope)],
        "metrics": platform.metrics.snapshot(),
    }
