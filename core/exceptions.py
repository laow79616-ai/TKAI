"""
TKAI Core Exceptions

Issue-003.1
"""

from __future__ import annotations


class TKAIError(Exception):
    """
    Base exception for all TKAI errors.
    """

    default_message = "An unknown TKAI error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ConfigError(TKAIError):
    """Configuration related error."""

    default_message = "Configuration error."


class ProjectError(TKAIError):
    """Project related error."""

    default_message = "Project error."


class WorkspaceError(TKAIError):
    """Workspace related error."""

    default_message = "Workspace error."


class TemplateError(TKAIError):
    """Template engine error."""

    default_message = "Template error."


class GeneratorError(TKAIError):
    """Generator error."""

    default_message = "Generator error."


class PluginError(TKAIError):
    """Plugin system error."""

    default_message = "Plugin error."


class WorkflowError(TKAIError):
    """Workflow engine error."""

    default_message = "Workflow error."


class AIProviderError(TKAIError):
    """AI provider error."""

    default_message = "AI provider error."


class RegistryError(TKAIError):
    """Registry error."""

    default_message = "Registry error."


class ValidationError(TKAIError):
    """Validation error."""

    default_message = "Validation failed."


class FileSystemError(TKAIError):
    """Filesystem related error."""

    default_message = "Filesystem error."


class CommandError(TKAIError):
    """CLI command execution error."""

    default_message = "Command execution failed."