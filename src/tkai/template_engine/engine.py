"""
Template Engine
"""

from pathlib import Path

from .loader import TemplateLoader
from .renderer import TemplateRenderer
from .variables import build_variables


class TemplateEngine:
    """Render a project template into a target directory."""

    def __init__(self):
        self.loader = TemplateLoader()
        self.renderer = TemplateRenderer()

    def render(
        self,
        template: str,
        project_name: str,
        output_dir: Path,
    ):

        template_dir = self.loader.load(template)

        variables = build_variables(
            project_name,
            template,
        )

        for source in template_dir.rglob("*"):

            relative = source.relative_to(template_dir)

            target = output_dir / relative

            if source.is_dir():
                target.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                continue

            self.renderer.render_file(
                source,
                target,
                variables,
            )