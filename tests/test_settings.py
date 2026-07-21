import os

from tkai.core.settings import Settings


def test_defaults():
    settings = Settings({"app": {"name": "TKAI"}})

    assert settings.get("app.name") == "TKAI"


def test_set():
    settings = Settings()

    settings.set("core.debug", True)

    assert settings.get("core.debug") is True


def test_merge():
    settings = Settings({"core": {"debug": False}})

    settings.merge({"core": {"debug": True}})

    assert settings.get("core.debug") is True


def test_reset():
    settings = Settings({"debug": False})

    settings.set("debug", True)

    settings.reset()

    assert settings.get("debug") is False


def test_environment(monkeypatch):
    monkeypatch.setenv("TKAI_CORE_DEBUG", "true")

    settings = Settings()

    settings.load_environment()

    assert settings.get("core.debug") == "true"