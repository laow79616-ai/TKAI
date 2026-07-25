"""Safe built-in workflow examples."""

from .models import WorkflowDefinition
from .task import Step, Task


def definitions() -> list[WorkflowDefinition]:
    hello = Step(Task("hello", lambda ctx: f"hello {ctx.get('name', 'world')}"))
    serial = [
        Step(Task("first", lambda _: 1)),
        Step(
            Task("second", lambda ctx: ctx["previous_result"][0] + 1),
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
    checkpoint = [
        Step(Task("capture", lambda ctx: dict(ctx.get("results", {})))),
        Step(
            Task("continue", lambda ctx: "resumable"),
            dependencies=("capture",),
        ),
    ]
    pause_resume = [
        Step(Task("prepare", lambda _: "prepared")),
        Step(
            Task("finish", lambda ctx: f"{ctx['previous_result']}-finished"),
            dependencies=("prepare",),
        ),
    ]
    return [
        WorkflowDefinition("hello-workflow", [hello]),
        WorkflowDefinition("serial-example", serial),
        WorkflowDefinition("parallel-example", parallel),
        WorkflowDefinition("conditional-example", conditional),
        WorkflowDefinition("retry-example", [retry]),
        WorkflowDefinition("checkpoint-example", checkpoint),
        WorkflowDefinition("pause-resume-example", pause_resume),
    ]
