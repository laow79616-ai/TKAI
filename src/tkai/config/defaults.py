"""
TKAI default configuration.
"""

DEFAULT_CONFIG = {
    "workspace": "~/Projects",
    "language": "zh-CN",
    "template": "fastapi",
    "llm": {
        "provider": "openai",
        "model": "gpt-5.5",
    },
    "plugin": {
        "auto_load": True,
    },
    "telemetry": False,
}