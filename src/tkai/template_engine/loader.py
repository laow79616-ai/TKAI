"""
Template Loader
"""

from pathlib import Path


class TemplateLoader:

    def __init__(self):

        self.root = Path(__file__).resolve().parents[3]

        self.templates = self.root / "templates"

    def load(self, template_name: str) -> Path:

        template = self.templates / template_name

        if not template.exists():

            raise FileNotFoundError(
                f"Template '{template_name}' not found."
            )

        return template