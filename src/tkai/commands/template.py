from tkai.template_engine import TemplateManager


def run(args):
    manager = TemplateManager()

    if args.action == "list":
        templates = manager.list_templates()

        print()
        print("=" * 50)
        print("Available Templates")
        print("=" * 50)
        print()

        for item in templates:
            print(f"✓ {item['name']}")
            print(f"  {item['description']}")
            print()