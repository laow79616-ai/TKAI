"""Studio configuration tests use explicit mappings only."""

from __future__ import annotations

import pytest

from studio.config import StudioConfigurationError, StudioSettings


def test_settings_mapping_is_explicit_validated_and_does_not_mutate_input() -> None:
    """Configuration construction requires no ambient environment access."""
    values: dict[str, object] = {"port": 8090, "api_prefix": "/studio"}
    settings = StudioSettings.from_mapping(values)

    values["port"] = 9000

    assert settings.port == 8090
    assert settings.api_prefix == "/studio"
    with pytest.raises(StudioConfigurationError, match="Unknown"):
        StudioSettings.from_mapping({"unknown": True})


def test_settings_reject_invalid_network_shape_without_binding_a_socket() -> None:
    """Validation covers configuration only and never starts a backend listener."""
    with pytest.raises(StudioConfigurationError, match="port"):
        StudioSettings(port=0)
