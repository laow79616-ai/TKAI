"""Local Plugin SDK hook example without discovery or external services."""

from __future__ import annotations

from tkai.plugins import Hook, PluginManager, PluginMetadata


class _ExamplePlugin:
    """Small deterministic SDK plugin used exclusively by this example."""

    def __init__(self, calls: list[str]) -> None:
        self.calls = calls

    def initialize(self) -> None:
        self.calls.append("initialize")

    def shutdown(self) -> None:
        self.calls.append("shutdown")

    def on_hook(self, hook: Hook, payload: dict[str, object]) -> None:
        self.calls.append(f"{hook.value}:{payload['message']}")


def run() -> list[str]:
    """Register, dispatch, and unload one local SDK plugin explicitly."""
    calls: list[str] = []
    manager = PluginManager()
    manager.register_sdk(_ExamplePlugin(calls), PluginMetadata("example", "1"))
    manager.dispatch(Hook.BEFORE_REQUEST, {"message": "ok"})
    manager.unload_sdk("example")
    return calls


if __name__ == "__main__":
    print(run())
