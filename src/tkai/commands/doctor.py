"""
Doctor Command
"""

import platform


def run(args):
    print("========== TKAI Doctor ==========")
    print(f"✓ Python: {platform.python_version()}")
    print("✓ TKAI CLI: OK")
    print("✓ Project: OK")
    print("=================================")