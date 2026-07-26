"""Route resolution for all enterprise execution targets."""

from collections.abc import Callable
from typing import Any

from ..models import PlanStep, RouteType

Handler = Callable[[PlanStep, dict[str, Any]], Any]


class Router:
    def __init__(self) -> None:
        self._handlers: dict[RouteType, Handler] = {}

    def register(self, route: RouteType, handler: Handler) -> None:
        self._handlers[route] = handler

    def resolve(self, step: PlanStep) -> Handler:
        try:
            return self._handlers[step.route]
        except KeyError as error:
            raise LookupError(f"No handler for {step.route.value}.") from error
