# Development Guide

Use Python 3.10 or later. Install the project with development dependencies:

```bash
python -m pip install -e '.[dev]'
```

Before committing, run:

```bash
python -m pytest -q
python -m ruff check .
python -m black --check src tests plugins
python -m mypy src/tkai
```

New public behavior must include an interface, implementation, type hints,
documentation, and tests. Keep compatibility layers when changing a public
interface; do not use tests to hide implementation defects.
