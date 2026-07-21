"""
TKAI Command Line Interface
"""

import argparse
import shutil
import sys
from pathlib import Path
from . import __version__


def cmd_version():
    print(f"TKAI v{__version__}")


def check_tool(name):
    return shutil.which(name) is not None


def cmd_doctor():
    print("=" * 50)
    print("TKAI Doctor")
    print("=" * 50)

    print(f"Python Version : {sys.version.split()[0]}")
    print(f"Git            : {'OK' if check_tool('git') else 'Not Found'}")
    print(f"PowerShell     : {'OK' if check_tool('powershell') or check_tool('pwsh') else 'Not Found'}")

    project_ok = (
        Path("src").exists()
        and Path("docs").exists()
        and Path("templates").exists()
    )

    print(f"Project        : {'OK' if project_ok else 'Incomplete'}")
    print("=" * 50)


def show_banner():
    print("=" * 50)
    print(f"TKAI v{__version__}")
    print("AI Software Factory")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        prog="tkai",
        description="TKAI AI Software Factory"
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version"
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("doctor", help="Check development environment")

    args = parser.parse_args()

    if args.version:
        cmd_version()
        return

    if args.command == "doctor":
        cmd_doctor()
        return

    show_banner()
    parser.print_help()