from pathlib import Path

from tkai.template_engine import TemplateEngine


class ProjectGenerator:

    def __init__(self):
        self.engine = TemplateEngine()

    def create(
        self,
        project_name: str,
        template: str = "fastapi",
    ):

        target = Path.cwd() / project_name

        if target.exists():
            raise FileExistsError(
                f"Project '{project_name}' already exists."
            )

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