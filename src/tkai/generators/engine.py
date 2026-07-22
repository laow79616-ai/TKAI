"""
TKAI Generator Engine
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .hooks import HookManager
from .scaffold import Scaffold
from .variables import VariableManager


class GeneratorEngine:
    """Generator execution engine."""

    def __init__(
        self,
        template_dir: str | Path,
    ) -> None:
        self.template_dir = Path(template_dir)

        if not self.template_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found: {self.template_dir}"
            )

        self.variables = VariableManager()
        self.hooks = HookManager()
        self.scaffold = Scaffold(self.template_dir)

    def register_hook(
        self,
        event: str,
        func,
    ) -> None:
        self.hooks.register(event, func)

    def unregister_hook(
        self,
        event: str,
        func,
    ) -> None:
        self.hooks.unregister(event, func)

    def generate(
        self,
        output: str | Path,
        variables: dict[str, Any] | None = None,
    ) -> Path:
        if variables:
            self.variables.merge(variables)

        self.hooks.run(
            "pre_generate",
            self.variables.to_dict(),
        )

        result = self.scaffold.generate(
            output,
            self.variables.to_dict(),
        )

        self.hooks.run(
            "post_generate",
            result,
            self.variables.to_dict(),
        )

        return result