from typer.testing import CliRunner

from tkai.cli import app

runner = CliRunner()


def test_info():
    result = runner.invoke(
        app,
        ["info"],
    )

    assert result.exit_code == 0
    assert "TKAI" in result.stdout


def test_help():
    result = runner.invoke(
        app,
        ["--help"],
    )

    assert result.exit_code == 0


def test_version_command():
    result = runner.invoke(
        app,
        [
            "version",
            "--help",
        ],
    )

    assert result.exit_code == 0