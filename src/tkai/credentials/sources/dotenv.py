"""Small local .env credential source; it never mutates process environment."""

from __future__ import annotations

from pathlib import Path

from .env import EnvironmentCredentialProvider


class DotenvCredentialProvider(EnvironmentCredentialProvider):
    """Load known credentials from a caller-selected local dotenv file."""

    def __init__(self, path: Path | str | None = None, text: str | None = None) -> None:
        self._path = Path(path) if path is not None else None
        self._text = text
        super().__init__({})
        self.reload()

    def identifier(self) -> str:
        """Return the safe local-source name."""
        return "dotenv"

    def reload(self) -> None:
        """Reload local dotenv text without exporting it to process environment."""
        text = self._text
        if text is None and self._path is not None and self._path.exists():
            text = self._path.read_text(encoding="utf-8")
        self._environment = self._parse(text or "")

    @staticmethod
    def _parse(text: str) -> dict[str, str]:
        """Parse simple ``KEY=VALUE`` lines, comments, and optional quotes."""
        values: dict[str, str] = {}
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().removeprefix("export ").strip()
            value = value.strip().strip('"').strip("'")
            if key:
                values[key] = value
        return values
