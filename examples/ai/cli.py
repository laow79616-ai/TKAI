"""CLI invocation example using an isolated service and no external provider."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from tkai.ai import ProviderManager
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands


def run() -> dict[str, object]:
    """Run the public ``tkai ai version --json`` command in isolation."""
    previous = ai_commands._service
    ai_commands._service = AICommandService(ProviderManager())
    try:
        result = CliRunner().invoke(ai_commands.app, ["version", "--json"])
    finally:
        ai_commands._service = previous
    if result.exit_code != 0:
        raise RuntimeError("AI CLI version example failed")
    return json.loads(result.stdout)


if __name__ == "__main__":
    print(run())
