"""
TKAI Template Renderer
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import StrictUndefined
from jinja2 import Template


class TemplateRenderer:
    """Render Jinja2 templates."""

    def __init__(
        self,
        template_dir: str | Path | None = None,
        *,
        strict: bool = True,
    ) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir))
            if template_dir
            else None,
            undefined=StrictUndefined if strict else None,
            keep_trailing_newline=True,
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @property
    def environment(self) -> Environment:
        return self._env

    def render_string(
        self,
        content: str,
        variables: dict[str, Any],
    ) -> str:
        template: Template = self._env.from_string(content)
        return template.render(**variables)

    def render_file(
        self,
        template_name: str,
        variables: dict[str, Any],
    ) -> str:
        template = self._env.get_template(template_name)
        return template.render(**variables)

    def render_to_file(
        self,
        template_name: str,
        output_file: str | Path,
        variables: dict[str, Any],
    ) -> Path:
        output = Path(output_file)
        output.parent.mkdir(parents=True, exist_ok=True)

        rendered = self.render_file(template_name, variables)

        output.write_text(
            rendered,
            encoding="utf-8",
        )

        return output

    def add_filter(
        self,
        name: str,
        func,
    ) -> None:
        self._env.filters[name] = func

    def add_global(
        self,
        name: str,
        value: Any,
    ) -> None:
        self._env.globals[name] = value