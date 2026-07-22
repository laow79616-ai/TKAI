"""Safe built-in workflow examples."""

from .models import WorkflowDefinition
from .task import Step, Task


def definitions() -> list[WorkflowDefinition]:
    hello = Step(Task("hello", lambda ctx: f"hello {ctx.get('name', 'world')}"))
    serial = [
        Step(Task("first", lambda _: 1)),
        Step(
            Task("second", lambda ctx: ctx["previous_result"] + 1),
            dependencies=("first",),
        ),
    ]
    parallel = [
        Step(Task("left", lambda _: "left")),
        Step(Task("right", lambda _: "right")),
    ]
    conditional = [
        Step(
            Task("enabled", lambda _: "yes"),
            condition=lambda ctx: bool(ctx.get("enabled")),
        )
    ]
    retry = Step(Task("retry", lambda _: "done"), retries=1)
    return [
        WorkflowDefinition("hello-workflow", [hello]),
        WorkflowDefinition("serial-example", serial),
        WorkflowDefinition("parallel-example", parallel),
        WorkflowDefinition("conditional-example", conditional),
        WorkflowDefinition("retry-example", [retry]),
    ]
