"""
Template Renderer
"""

from pathlib import Path


class TemplateRenderer:

    def render_text(
        self,
        text: str,
        variables: dict,
    ):

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
        variables: dict,
    ):

        text = source.read_text(
            encoding="utf-8"
        )

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