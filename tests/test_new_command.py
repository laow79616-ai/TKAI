from pathlib import Path

from typer.testing import CliRunner

from tkai.commands.new import app

runner = CliRunner()


def test_new_project(tmp_path: Path):
    template = (
        Path("src")
        / "tkai"
        / "templates"
        / "default"
    )

    assert template.exists()

    result = runner.invoke(
        app,
        [
            "demo",
        ],
    )

    assert result.exit_code == 0