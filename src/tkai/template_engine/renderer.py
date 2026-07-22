"""
Template Renderer
"""

from pathlib import Path
from typing import Any


class TemplateRenderer:
    """Render the lightweight legacy ``{{ name }}`` template syntax."""

    def render_text(
        self,
        text: str,
        variables: dict[str, Any],
    ) -> str:

        for key, value in variables.items():

            text = text.replace(
                "{{ " + key + " }}",
                str(value),
            )

        return text

    def render_file(
        self,
        source: Path,
        target: Path,
        variables: dict[str, Any],
    ) -> Path:

        text = source.read_text(encoding="utf-8")

        text = self.render_text(
            text,
            variables,
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            text,
            encoding="utf-8",
        )
        return target
