"""Extensible provider capability declarations for the V2 SDK."""

from __future__ import annotations

from enum import Enum


class ProviderCapability(str, Enum):
    """Common capability names without binding to a concrete model vendor."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    IMAGE = "image"
    AUDIO = "audio"
    TOOL_CALLING = "tool_calling"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"
    STRUCTURED_OUTPUT = "structured_output"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
