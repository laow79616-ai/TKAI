"""Provider configuration loading without SDK dependencies."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from .errors import ProviderConfigurationError
from .models import ProviderConfig

_ENV = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")


def _expand(value: Any) -> Any:
    if isinstance(value, str):

        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in os.environ:
                raise ProviderConfigurationError(
                    f"Missing environment variable: {name}"
                )
            return os.environ[name]

        return _ENV.sub(replace, value)
    if isinstance(value, dict):
        return {key: _expand(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand(item) for item in value]
    return value


def load_provider_config(
    source: dict[str, Any] | Path | str,
) -> tuple[str | None, list[ProviderConfig]]:
    """Load YAML/JSON providers configuration with strict environment expansion."""
    if isinstance(source, (Path, str)):
        path = Path(source)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError, json.JSONDecodeError) as exc:
            raise ProviderConfigurationError("Invalid provider configuration") from exc
    else:
        data = source
    providers = _expand(data.get("providers", data))
    if not isinstance(providers, dict):
        raise ProviderConfigurationError("providers must be an object")
    default = providers.pop("default", None)
    configs: list[ProviderConfig] = []
    for name, raw in providers.items():
        if not isinstance(raw, dict):
            raise ProviderConfigurationError(f"Provider '{name}' must be an object")
        raw = dict(raw)
        raw.setdefault("name", name)
        raw.setdefault("type", name)
        if "http_referer" in raw:
            raw.setdefault("headers", {})["HTTP-Referer"] = raw.pop("http_referer")
        if "app_title" in raw:
            raw.setdefault("headers", {})["X-Title"] = raw.pop("app_title")
        try:
            config = ProviderConfig(**raw)
            config.validate()
        except (TypeError, ValueError) as exc:
            raise ProviderConfigurationError(f"Invalid provider '{name}'") from exc
        configs.append(config)
    if default is not None and default not in {item.name for item in configs}:
        raise ProviderConfigurationError("Default provider is not configured")
    return default, configs
