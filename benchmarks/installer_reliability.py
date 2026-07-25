"""Bounded offline Installer Reliability benchmark reporting Markdown and JSON."""

from __future__ import annotations

from .base import BenchmarkRunner
from .report import BenchmarkReport


def run() -> dict[str, str]:
    """Measure a pure-memory single-install path with no real package operation."""
    from marketplace.installer import ReferenceInstallerService
    from tests.marketplace.installer.test_core import request

    result = BenchmarkRunner(iterations=3, random_seed=0).run(
        lambda: ReferenceInstallerService().install(request())
    )
    return {
        "markdown": BenchmarkReport.to_markdown("installer-reliability", result),
        "json": BenchmarkReport.to_json("installer-reliability", result),
    }


if __name__ == "__main__":
    print(run()["markdown"])
