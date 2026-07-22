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

## Workflow runtime release checks

Workflow changes must exercise both public CLI paths and runtime recovery.
Run `tkai workflow doctor`, execute every built-in example, and cover JSON and
YAML input, checkpoint export/import, pause/resume, cancellation, and async
parallel control. A release candidate requires all of the following:

```bash
python -m pytest -q
python -m ruff check .
python -m black --check .
python -m mypy src
```

Provider tests must inject a transport or SDK fake. Do not add tests that call
real provider endpoints or include a credential in source, fixture output, or
an assertion message.
