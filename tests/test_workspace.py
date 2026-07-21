from pathlib import Path

from tkai.core.workspace import Workspace


def test_workspace_create(tmp_path: Path):
    workspace = Workspace(root=tmp_path / "demo")

    assert workspace.exists() is False

    workspace.create()

    assert workspace.exists() is True
    assert workspace.root.is_dir()


def test_workspace_initialize(tmp_path: Path):
    workspace = Workspace(root=tmp_path / "demo")

    workspace.initialize()

    for directory in workspace.directories:
        assert (workspace.root / directory).exists()


def test_workspace_resolve(tmp_path: Path):
    workspace = Workspace(root=tmp_path)

    path = workspace.resolve("cache", "a.txt")

    assert path == tmp_path / "cache" / "a.txt"


def test_workspace_ensure_dir(tmp_path: Path):
    workspace = Workspace(root=tmp_path)

    logs = workspace.ensure_dir("logs")

    assert logs.exists()
    assert logs.is_dir()


def test_workspace_clean(tmp_path: Path):
    workspace = Workspace(root=tmp_path)

    workspace.initialize()

    (workspace.root / "cache" / "test.txt").write_text("1")
    (workspace.root / "temp" / "test.txt").write_text("1")
    (workspace.root / "output" / "test.txt").write_text("1")

    workspace.clean()

    assert not (workspace.root / "cache").exists()
    assert not (workspace.root / "temp").exists()
    assert not (workspace.root / "output").exists()


def test_workspace_remove(tmp_path: Path):
    workspace = Workspace(root=tmp_path / "demo")

    workspace.initialize()

    assert workspace.exists()

    workspace.remove()

    assert workspace.exists() is False