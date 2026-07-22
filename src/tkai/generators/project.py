"""High-level compatibility generator for project templates."""

from __future__ import annotations

from pathlib import Path

from tkai.template_engine import TemplateEngine


class ProjectGenerator:
    """Create a project using the legacy template-engine interface."""

    def __init__(self) -> None:
        self.engine = TemplateEngine()

    def create(
        self,
        project_name: str,
        template: str = "fastapi",
    ) -> None:
        """Create a project in the current working directory."""

        target = Path.cwd() / project_name

        if target.exists():
            raise FileExistsError(f"Project '{project_name}' already exists.")

        self.engine.render(
            template=template,
            project_name=project_name,
            output_dir=target,
        )

        print()
        print("=" * 50)
        print("TKAI Project Generator")
        print("=" * 50)
        print(f"Project : {project_name}")
        print(f"Template: {template}")
        print(f"Location: {target}")
        print()
        print("Project created successfully.")
