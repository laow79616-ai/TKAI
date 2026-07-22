"""
Project Generator
"""

import shutil
from pathlib import Path


class ProjectGenerator:
    """Generate projects from templates."""

    def __init__(self):
        # TKAI/
        self.project_root = Path(__file__).resolve().parents[3]

        # TKAI/templates
        self.template_root = self.project_root / "templates"

    def create(self, project_name: str, template: str = "fastapi"):

        template_path = self.template_root / template

        if not template_path.exists():
            raise FileNotFoundError(
                f"Template '{template}' does not exist."
            )

        target = Path.cwd() / project_name

        if target.exists():
            raise FileExistsError(
                f"Project '{project_name}' already exists."
            )

        shutil.copytree(template_path, target)

        print()
        print("===================================")
        print(" Project created successfully")
        print("===================================")
        print(f" Project : {project_name}")
        print(f" Template: {template}")
        print(f" Path    : {target}")
        print("===================================")