"""Explicit, injected configuration-loader coverage without process environment use."""

from __future__ import annotations

from tkai.sdk.configuration import (
    CompositeConfigurationLoader,
    EnvironmentConfigurationLoader,
    MappingConfigurationLoader,
)


def test_mapping_environment_and_composite_precedence_are_immutable() -> None:
    """Later injected sources override earlier values without modifying their inputs."""
    mapping = {"timeout": 5, "model": "local"}
    configuration = CompositeConfigurationLoader(
        (
            MappingConfigurationLoader(mapping),
            EnvironmentConfigurationLoader(environment={"TKAI_TIMEOUT": "30"}),
        )
    ).load()

    assert configuration.get("timeout") == "30"
    assert configuration.get("model") == "local"
    assert mapping == {"timeout": 5, "model": "local"}
