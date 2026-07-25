"""Allow-listed production configuration without implicit unknown environment reads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


class ProductionConfigurationError(ValueError):
    """Raised when an explicitly supplied production setting is invalid."""


@dataclass(frozen=True, slots=True)
class ProductionConfiguration:
    """Validated configuration for local production hardening components."""

    log_level: str = "INFO"
    rate_limit_requests: int = 120
    rate_limit_window_seconds: float = 60.0
    security_headers_enabled: bool = True

    def __post_init__(self) -> None:
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            raise ProductionConfigurationError("log_level must be a supported level.")
        if self.rate_limit_requests < 1:
            raise ProductionConfigurationError("rate_limit_requests must be positive.")
        if self.rate_limit_window_seconds <= 0:
            raise ProductionConfigurationError(
                "rate_limit_window_seconds must be positive."
            )


class ProductionConfigurationLoader:
    """Merge a caller-supplied .env mapping with an allow-listed environment mapping."""

    _keys = {
        "TKAI_LOG_LEVEL",
        "TKAI_RATE_LIMIT_REQUESTS",
        "TKAI_RATE_LIMIT_WINDOW_SECONDS",
        "TKAI_SECURITY_HEADERS_ENABLED",
    }

    @classmethod
    def load(
        cls,
        *,
        dotenv_path: Path | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> ProductionConfiguration:
        """Load only known values; supplied environment values override .env values."""
        values = cls._read_dotenv(dotenv_path) if dotenv_path is not None else {}
        if environment is not None:
            values.update(
                {key: environment[key] for key in cls._keys if key in environment}
            )
        return ProductionConfiguration(
            log_level=values.get("TKAI_LOG_LEVEL", "INFO").upper(),
            rate_limit_requests=cls._integer(values, "TKAI_RATE_LIMIT_REQUESTS", 120),
            rate_limit_window_seconds=cls._float(
                values, "TKAI_RATE_LIMIT_WINDOW_SECONDS", 60.0
            ),
            security_headers_enabled=cls._boolean(
                values, "TKAI_SECURITY_HEADERS_ENABLED", True
            ),
        )

    @classmethod
    def _read_dotenv(cls, path: Path) -> dict[str, str]:
        values: dict[str, str] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            if not separator or key not in cls._keys:
                raise ProductionConfigurationError(
                    "Only known TKAI production settings are allowed in .env files."
                )
            values[key] = value.strip()
        return values

    @staticmethod
    def _integer(values: Mapping[str, str], key: str, default: int) -> int:
        try:
            return int(values.get(key, str(default)))
        except ValueError as error:
            raise ProductionConfigurationError(f"{key} must be an integer.") from error

    @staticmethod
    def _float(values: Mapping[str, str], key: str, default: float) -> float:
        try:
            return float(values.get(key, str(default)))
        except ValueError as error:
            raise ProductionConfigurationError(f"{key} must be a number.") from error

    @staticmethod
    def _boolean(values: Mapping[str, str], key: str, default: bool) -> bool:
        value = values.get(key)
        if value is None:
            return default
        if value.lower() in {"1", "true", "yes"}:
            return True
        if value.lower() in {"0", "false", "no"}:
            return False
        raise ProductionConfigurationError(f"{key} must be a boolean.")
