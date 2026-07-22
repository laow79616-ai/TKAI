"""
TKAI CLI
AI Software Factory Command Line Interface
"""

from __future__ import annotations

import typer

from tkai import __version__
from tkai.commands.new import app as new_app
from tkai.commands.template import app as template_app
from tkai.commands.version import app as version_app
from tkai.commands.doctor import app as doctor_app
from tkai.commands.init import app as init_app

app = typer.Typer(
    name="tkai",
    help="TKAI AI Software Factory",
    add_completion=False,
    no_args_is_help=True,
)

app.add_typer(
    new_app,
    name="new",
)

app.add_typer(
    template_app,
    name="template",
)

app.add_typer(
    version_app,
    name="version",
)

app.add_typer(
    doctor_app,
    name="doctor",
)

app.add_typer(
    init_app,
    name="init",
)


@app.command()
def info() -> None:
    """
    Show TKAI information.
    """

    typer.echo(f"TKAI v{__version__}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()