"""
TKAI Core Exceptions

Copyright (c) TKAI
"""

from __future__ import annotations


class TKAIError(Exception):
    """Base exception for all TKAI errors."""


class ConfigError(TKAIError):
    """Configuration error."""


class ProjectError(TKAIError):
    """Project error."""


class WorkspaceError(TKAIError):
    """Workspace error."""


class RegistryError(TKAIError):
    """Registry error."""


class SettingsError(TKAIError):
    """Settings error."""


class ContextError(TKAIError):
    """Context error."""


class LifecycleError(TKAIError):
    """Lifecycle error."""


class TemplateError(TKAIError):
    """Template error."""


class GeneratorError(TKAIError):
    """Generator error."""


class PluginError(TKAIError):
    """Plugin error."""


class WorkflowError(TKAIError):
    """Workflow error."""


class AIProviderError(TKAIError):
    """AI provider error."""


class ValidationError(TKAIError):
    """Validation error."""


class FileSystemError(TKAIError):
    """Filesystem error."""