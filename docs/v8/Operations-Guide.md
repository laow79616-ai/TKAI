# Hyper Kernel Operations Guide

Use `/v8/kernel` for identity and registry counts, `/v8/frameworks`,
`/v8/capabilities`, and `/v8/runtime` for discovery, and `/v8/health`,
`/v8/metrics`, and `/v8/diagnostics` for operations. These routes are read-only.

Health is aggregated from metadata published during registration. The kernel
does not actively probe or execute a provider. Unknown health is expected until
a framework publishes status. Diagnostics identify missing required dependency
references. Audit and logs redact likely secret fields.

Run focused checks with:

```text
python -m pytest tests/v8/hyper_kernel
python -m ruff check src/tkai/v8 tests/v8
python -m mypy
```
