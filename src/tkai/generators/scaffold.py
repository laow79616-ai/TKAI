"""
TKAI Scaffold Engine
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .renderer import TemplateRenderer


class Scaffold:
    """Generate a project from a template directory."""

    def __init__(self, template_dir: str | Path) -> None:
        self.template_dir = Path(template_dir)
        self.renderer = TemplateRenderer(self.template_dir)

    def generate(
        self,
        output_dir: str | Path,
        variables: dict,
    ) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for item in self.template_dir.rglob("*"):
            relative = item.relative_to(self.template_dir)

            rendered_name = self.renderer.render_string(
                str(relative),
                variables,
            )

            destination = output_dir / rendered_name

            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue

            destination.parent.mkdir(parents=True, exist_ok=True)

            if item.suffix in {
                ".j2",
                ".jinja",
                ".jinja2",
                ".tmpl",
            }:
                template_name = relative.as_posix()

                content = self.renderer.render_file(
                    template_name,
                    variables,
                )

                destination = destination.with_suffix("")

                destination.write_text(
                    content,
                    encoding="utf-8",
                )
            else:
                shutil.copy2(
                    item,
                    destination,
                )

        return output_dir