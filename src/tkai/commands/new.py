"""
TKAI New Project Command
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import typer

from tkai.generators import GeneratorEngine

app = typer.Typer(
    help="Create a new project from a template.",
)


def run(args) -> None:
    """
    Compatibility entry for argparse CLI.
    """

    namespace = SimpleNamespace(
        project=getattr(args, "project_name", None),
        template=getattr(args, "template", "default"),
    )

    if not namespace.project:
        raise SystemExit("Project name is required.")

    create(
        project=namespace.project,
        template=namespace.template,
    )


@app.command(name="new")
def create(
    project: str = typer.Argument(
        ...,
        help="Project name.",
    ),
    template: str = typer.Option(
        "default",
        "--template",
        "-t",
        help="Template name.",
    ),
) -> None:
    """
    Create a new project.
    """

    template_dir = (
        Path(__file__).parent.parent
        / "templates"
        / template
    )

    output = Path.cwd() / project

    engine = GeneratorEngine(template_dir)

    engine.generate(
        output=output,
        variables={
            "project_name": project,
        },
    )

    typer.secho(
        f"✔ Project created: {output}",
        fg=typer.colors.GREEN,
    )