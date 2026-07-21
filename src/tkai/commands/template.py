"""
TKAI Template Command
"""

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
            print(f"  {item.get('description', 'No description')}")
            print()

    elif args.action == "info":

        info = manager.get_template(args.template_name)

        print()
        print("=" * 50)
        print("Template Information")
        print("=" * 50)
        print()

        print(f"Name        : {info['name']}")
        print(f"Display     : {info.get('display_name', '-')}")
        print(f"Version     : {info.get('version', '-')}")
        print(f"Author      : {info.get('author', '-')}")
        print(f"Python      : {info.get('python', '-')}")
        print()

        print("Description")
        print("-" * 50)
        print(info.get("description", ""))
        print()

        print("Tags")
        print("-" * 50)
        print(", ".join(info.get("tags", [])))
        print()

    elif args.action == "validate":

        results = manager.validate_all()

        print()
        print("=" * 50)
        print("Checking Templates")
        print("=" * 50)
        print()

        passed = 0
        failed = 0

        for result in results:

            if result["valid"]:
                print(f"✓ {result['name']}")
                passed += 1

            else:
                print(f"✗ {result['name']}")
                for error in result["errors"]:
                    print(f"  - {error}")
                failed += 1

            print()

        print("-" * 50)
        print(f"Templates : {len(results)}")
        print(f"Passed    : {passed}")
        print(f"Failed    : {failed}")
        print()