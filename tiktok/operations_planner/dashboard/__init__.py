"""Dashboard projection for the operations planner."""

from ..models import PlannerScope
from ..service import TikTokAIOperationsPlanner


def planner_dashboard(
    service: TikTokAIOperationsPlanner, scope: PlannerScope
) -> dict[str, object]:
    return service.dashboard(scope)
