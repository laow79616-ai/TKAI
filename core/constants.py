"""
TKAI Core Constants

Issue-003.2
"""

from __future__ import annotations

from pathlib import Path

# ----------------------------------------------------------------------
# Application
# ----------------------------------------------------------------------

APP_NAME = "TKAI"

APP_FULL_NAME = "TKAI AI Software Factory"

APP_VERSION = "0.1.0"

APP_AUTHOR = "TKAI Team"

# ----------------------------------------------------------------------
# Environment Variables
# ----------------------------------------------------------------------

ENV_DEBUG = "TKAI_DEBUG"

ENV_HOME = "TKAI_HOME"

ENV_CONFIG = "TKAI_CONFIG"

ENV_WORKSPACE = "TKAI_WORKSPACE"

ENV_PLUGIN_PATH = "TKAI_PLUGIN_PATH"

# ----------------------------------------------------------------------
# Directory Names
# ----------------------------------------------------------------------

TKAI_DIR = ".tkai"

CONFIG_DIR = ".tkai"

CACHE_DIR = ".cache"

LOG_DIR = "logs"

PLUGIN_DIR = "plugins"

TEMPLATE_DIR = "templates"

WORKFLOW_DIR = "workflows"

PROMPT_DIR = "prompts"

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

DEFAULT_CONFIG_FILE = "config.yaml"

DEFAULT_TEMPLATE = "fastapi"

DEFAULT_ENCODING = "utf-8"

# ----------------------------------------------------------------------
# Runtime
# ----------------------------------------------------------------------

DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_TIMEOUT = 30

DEFAULT_RETRY = 3

# ----------------------------------------------------------------------
# Files
# ----------------------------------------------------------------------

README_FILE = "README.md"

LICENSE_FILE = "LICENSE"

PYPROJECT_FILE = "pyproject.toml"

GITIGNORE_FILE = ".gitignore"

# ----------------------------------------------------------------------
# Home Paths
# ----------------------------------------------------------------------

HOME_DIR = Path.home()

TKAI_HOME = HOME_DIR / ".tkai"

USER_CONFIG_FILE = TKAI_HOME / "config.yaml"

PLUGIN_HOME = TKAI_HOME / "plugins"

CACHE_HOME = TKAI_HOME / "cache"

LOG_HOME = TKAI_HOME / "logs"

# ----------------------------------------------------------------------
# Workspace
# ----------------------------------------------------------------------

WORKSPACE_MARKER = ".tkai"

PROJECT_CONFIG = "tkai.yaml"

# ----------------------------------------------------------------------
# Template
# ----------------------------------------------------------------------

TEMPLATE_JSON = "template.json"

TEMPLATE_IGNORE = ".templateignore"

# ----------------------------------------------------------------------
# Plugin
# ----------------------------------------------------------------------

PLUGIN_MANIFEST = "plugin.json"

PLUGIN_ENTRY = "__init__.py"

# ----------------------------------------------------------------------
# Generator
# ----------------------------------------------------------------------

GENERATOR_CONFIG = "generator.yaml"

# ----------------------------------------------------------------------
# Workflow
# ----------------------------------------------------------------------

WORKFLOW_CONFIG = "workflow.yaml"

# ----------------------------------------------------------------------
# AI
# ----------------------------------------------------------------------

DEFAULT_PROVIDER = "openai"

DEFAULT_MODEL = "gpt-5.5"

# ----------------------------------------------------------------------
# Exit Codes
# ----------------------------------------------------------------------

EXIT_SUCCESS = 0

EXIT_FAILURE = 1

EXIT_CONFIG_ERROR = 2

EXIT_TEMPLATE_ERROR = 3

EXIT_PLUGIN_ERROR = 4

EXIT_WORKFLOW_ERROR = 5

EXIT_AI_ERROR = 6