# V1.0 Release Checklist

## Required validation

- [ ] `python -m pytest`
- [ ] `python -m ruff check .`
- [ ] `python -m black --check .`
- [ ] `python -m mypy src`
- [ ] Run every `examples/ai/*.py` example offline.
- [ ] Review public AI compatibility tests for AIClient, providers, sync,
      async, streaming, and CLI behavior.
- [ ] Review `README.md`, `docs/Architecture.md`, `docs/Migration.md`,
      `docs/Providers.md`, `docs/CLI.md`, and `docs/Doctor.md`.
- [ ] Check `git diff --check` and ensure `git status --short` is empty.

## Release metadata

Package metadata currently declares `1.0.0rc1` in `pyproject.toml`. This is
the V1.0 release-candidate preparation state. The release commit is tag-ready
after the checklist passes, but this repository does not create a Git tag as
part of validation.

## Release notes

V1.0 RC includes the stable core/config/template/generator/plugin/workflow
foundation and the provider-neutral AI framework: async transport adapters,
sync compatibility bridge, capability routing, independent fallback policy,
read-only Doctor diagnostics, and `tkai ai` inspection commands. All release
validation is offline and credentials are excluded from test output.
