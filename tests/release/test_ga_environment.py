from __future__ import annotations

import subprocess

from scripts import check_ga_environment


def test_command_version_uses_resolved_executable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(check_ga_environment.shutil, "which", lambda _: "npm.cmd")
    captured: list[tuple[str, ...]] = []

    def run(command: tuple[str, ...], **_: object) -> subprocess.CompletedProcess[str]:
        captured.append(command)
        return subprocess.CompletedProcess(command, 0, "10.0.0\n", "")

    monkeypatch.setattr(check_ga_environment.subprocess, "run", run)

    assert check_ga_environment.command_version(("npm", "--version")) == "10.0.0"
    assert captured == [("npm.cmd", "--version")]


def test_command_version_treats_spawn_failure_as_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(check_ga_environment.shutil, "which", lambda _: "tool.exe")

    def fail(*_: object, **__: object) -> subprocess.CompletedProcess[str]:
        raise OSError("cannot spawn")

    monkeypatch.setattr(check_ga_environment.subprocess, "run", fail)

    assert check_ga_environment.command_version(("tool", "--version")) is None
