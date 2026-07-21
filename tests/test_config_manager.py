from tkai.config.manager import ConfigManager


def test_load_default():
    cfg = ConfigManager()

    assert cfg.get("language") == "zh-CN"
    assert cfg.get("template") == "fastapi"
    assert cfg.get("workspace") == "~/Projects"
    assert cfg.get("llm.provider") == "openai"
    assert cfg.get("llm.model") == "gpt-5.5"


def test_get_default_value():
    cfg = ConfigManager()

    assert cfg.get("not_exists") is None
    assert cfg.get("not_exists", "default") == "default"


def test_set_value():
    cfg = ConfigManager()

    cfg.set("language", "en-US")

    assert cfg.get("language") == "en-US"


def test_set_nested_value():
    cfg = ConfigManager()

    cfg.set("llm.provider", "azure")

    assert cfg.get("llm.provider") == "azure"


def test_merge_simple():
    cfg = ConfigManager()

    cfg.merge(
        {
            "language": "ja-JP",
        }
    )

    assert cfg.get("language") == "ja-JP"


def test_merge_nested():
    cfg = ConfigManager()

    cfg.merge(
        {
            "llm": {
                "provider": "azure",
                "model": "gpt-4.1",
            }
        }
    )

    assert cfg.get("llm.provider") == "azure"
    assert cfg.get("llm.model") == "gpt-4.1"


def test_config_returns_copy():
    cfg = ConfigManager()

    data = cfg.config

    data["language"] = "changed"

    assert cfg.get("language") == "zh-CN"


def test_set_new_nested_key():
    cfg = ConfigManager()

    cfg.set("plugin.enable_cache", True)

    assert cfg.get("plugin.enable_cache") is True


def test_merge_add_new_section():
    cfg = ConfigManager()

    cfg.merge(
        {
            "database": {
                "host": "localhost",
                "port": 3306,
            }
        }
    )

    assert cfg.get("database.host") == "localhost"
    assert cfg.get("database.port") == 3306