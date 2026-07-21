"""
TKAI CLI
AI Software Factory Command Line Interface
"""

import argparse

from tkai.commands import doctor
from tkai.commands import version
from tkai.commands import new
from tkai.commands import init
from tkai.commands import template


def show_banner():
    print()
    print("=" * 60)
    print("TKAI AI Software Factory")
    print("=" * 60)
    print()


COMMANDS = {
    "doctor": doctor.run,
    "new": new.run,
    "init": init.run,
    "template": template.run,
}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="tkai",
        description="TKAI AI Software Factory"
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show TKAI version"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="<command>"
    )

    # doctor
    subparsers.add_parser(
        "doctor",
        help="Check development environment"
    )

    # new
    new_parser = subparsers.add_parser(
        "new",
        help="Create a new project"
    )

    new_parser.add_argument(
        "project_name",
        nargs="?",
        help="Project name"
    )

    new_parser.add_argument(
        "--template",
        default="fastapi",
        help="Project template"
    )

    # init
    subparsers.add_parser(
        "init",
        help="Initialize TKAI configuration"
    )

    # template
    template_parser = subparsers.add_parser(
        "template",
        help="Template management"
    )

    template_sub = template_parser.add_subparsers(
        dest="action",
        required=True
    )

    # template list
    template_sub.add_parser(
        "list",
        help="List templates"
    )

    # template info
    info_parser = template_sub.add_parser(
        "info",
        help="Show template information"
    )

    info_parser.add_argument(
        "template_name",
        help="Template name"
    )

    return parser


def main():
    parser = build_parser()

    args = parser.parse_args()

    if args.version:
        version.run(args)
        return

    if args.command in COMMANDS:
        COMMANDS[args.command](args)
        return

    show_banner()
    parser.print_help()


if __name__ == "__main__":
    main()