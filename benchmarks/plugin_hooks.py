"""Offline Plugin SDK hook-dispatch benchmark without plugin discovery."""

from __future__ import annotations

from _runner import BenchmarkResult, render, run

from tkai.plugins import Hook, PluginManager, PluginMetadata


class _Plugin:
    def initialize(self) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def on_hook(self, hook: Hook, payload: dict[str, object]) -> None:
        return None


def run_benchmark(iterations: int = 10_000) -> list[BenchmarkResult]:
    """Measure stable hook dispatch from zero through one hundred plugins."""
    results: list[BenchmarkResult] = []
    for plugin_count in (0, 1, 10, 100):
        manager = PluginManager()
        for number in range(plugin_count):
            manager.register_sdk(_Plugin(), PluginMetadata(f"plugin-{number}", "1"))
        results.append(
            run(
                f"plugin_hooks.dispatch.{plugin_count}",
                lambda manager=manager: manager.dispatch(
                    Hook.BEFORE_REQUEST, {"benchmark": True}
                ),
                iterations,
            )
        )
    return results


if __name__ == "__main__":
    print(render(run_benchmark()))
