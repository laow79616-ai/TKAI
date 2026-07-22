import asyncio

from tkai.workflow import Step, Task, WorkflowEngine


def test_async_parallel_respects_limit_and_order():
    running = 0
    peak = 0

    async def work(context):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.01)
        running -= 1
        return context["name"]

    steps = [Step(Task(f"s{index}", work)) for index in range(3)]
    results = asyncio.run(
        WorkflowEngine().run_async(steps, {"name": "ok"}, max_parallelism=2)
    )

    assert results == [["ok"], ["ok"], ["ok"]]
    assert peak == 2
