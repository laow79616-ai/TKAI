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
    "workflow": {
        "fail_fast": True,
        "max_parallelism": 4,
        "default_timeout": 30,
        "retry": {"max_attempts": 3, "delay": 0, "backoff": 1.0},
        "fail_fast_events": False,
    },
}
