"""Explicit local Studio server entry point; importing this module starts nothing."""

from __future__ import annotations

from importlib import import_module

from .app import create_studio_app
from .dependencies import StudioDependencies


def main() -> None:
    """Start uvicorn only after an operator explicitly runs this module."""
    try:
        uvicorn = import_module("uvicorn")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Uvicorn is required to run the Studio development host."
        ) from error
    dependencies = StudioDependencies.create()
    settings = dependencies.settings
    uvicorn.run(
        create_studio_app(dependencies=dependencies),
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
