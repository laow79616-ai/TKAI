"""
Template Loader
"""

from pathlib import Path


class TemplateLoader:
    """Locate repository-provided project templates."""

    def __init__(self, root: str | Path | None = None) -> None:
        self.root = (
            Path(root) if root is not None else Path(__file__).resolve().parents[3]
        )
        self.templates = self.root / "templates"

    def load(self, template_name: str) -> Path:
        """Return an existing template directory by name."""
        template = self.templates / template_name

        if not template.is_dir():
            raise FileNotFoundError(f"Template '{template_name}' not found.")

        return template
