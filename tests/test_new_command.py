from pathlib import Path

from typer.testing import CliRunner

import tkai
from tkai.commands.new import app

runner = CliRunner()


def test_new_project(tmp_path: Path, monkeypatch):
    template = Path(tkai.__file__).parent / "templates" / "default"

    assert template.exists()

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["demo"])

    assert result.exit_code == 0
    assert (tmp_path / "demo").exists()
