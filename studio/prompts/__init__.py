"""Versioned Prompt Studio with preview, diff, testing, and validation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import unified_diff
from re import findall
from threading import RLock

from studio.metrics import StudioMetrics


@dataclass(frozen=True, slots=True)
class PromptVersion:
    prompt_id: str
    version: int
    template: str
    variables: tuple[str, ...]
    created_at: datetime


class PromptStudio:
    """Keep append-only prompt history and deterministic local tooling."""

    def __init__(
        self, id_factory: Callable[[str], str], metrics: StudioMetrics | None = None
    ) -> None:
        self._id_factory = id_factory
        self._metrics = metrics or StudioMetrics()
        self._items: dict[str, list[PromptVersion]] = {}
        self._lock = RLock()

    def create(self, template: str) -> PromptVersion:
        prompt_id = self._id_factory("prompt")
        with self._lock:
            self._items[prompt_id] = []
        return self.version(prompt_id, template)

    def version(self, prompt_id: str, template: str) -> PromptVersion:
        variables = self.validate(template)
        with self._lock:
            history = self._items.setdefault(prompt_id, [])
            item = PromptVersion(
                prompt_id,
                len(history) + 1,
                template,
                variables,
                datetime.now(timezone.utc),
            )
            history.append(item)
        self._metrics.increment("prompt_versions")
        return item

    def history(self, prompt_id: str) -> tuple[PromptVersion, ...]:
        with self._lock:
            if prompt_id not in self._items:
                raise KeyError(f"Prompt not found: {prompt_id}")
            return tuple(self._items[prompt_id])

    def preview(
        self, prompt_id: str, variables: Mapping[str, object], version: int = -1
    ) -> str:
        selected = self.history(prompt_id)[version]
        missing = set(selected.variables).difference(variables)
        if missing:
            raise ValueError(f"Missing prompt variables: {', '.join(sorted(missing))}")
        result = selected.template
        for name in selected.variables:
            result = result.replace("{{" + name + "}}", str(variables[name]))
        return result

    def diff(self, prompt_id: str, left: int, right: int) -> str:
        history = self.history(prompt_id)
        return "".join(
            unified_diff(
                history[left - 1].template.splitlines(keepends=True),
                history[right - 1].template.splitlines(keepends=True),
                fromfile=f"v{left}",
                tofile=f"v{right}",
            )
        )

    def test(
        self,
        prompt_id: str,
        cases: tuple[tuple[Mapping[str, object], str], ...],
    ) -> tuple[bool, ...]:
        return tuple(
            expected in self.preview(prompt_id, variables)
            for variables, expected in cases
        )

    @staticmethod
    def validate(template: str) -> tuple[str, ...]:
        if not template.strip():
            raise ValueError("Prompt template is required.")
        pattern = r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}"
        stripped = template
        for token in findall(pattern, template):
            stripped = stripped.replace("{{" + token + "}}", "")
        if "{{" in stripped or "}}" in stripped:
            raise ValueError("Invalid prompt variable syntax.")
        return tuple(sorted(set(findall(pattern, template))))


__all__ = ("PromptStudio", "PromptVersion")
