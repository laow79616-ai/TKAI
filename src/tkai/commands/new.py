"""
New Project Command
"""

from tkai.generators import ProjectGenerator


def run(args):

    if not args.project_name:
        print("Usage:")
        print()
        print("    tkai new <project_name>")
        print()
        print("Example:")
        print("    tkai new Demo")
        return

    generator = ProjectGenerator()

    generator.create(
        project_name=args.project_name,
        template=args.template,
    )