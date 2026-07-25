# AI Doctor Guide

`DoctorService` is a read-only diagnostic service. It never initializes or
closes providers, sends HTTP requests, calls health endpoints, mutates the
registry, or changes fallback state.

`DoctorService.run()` checks environment, provider registry/default/aliases,
provider configuration metadata, capabilities and model overrides, transport
shape, runtime/adapter/SyncBridge wiring, and fallback policy/candidate state.
`validate_config()` intentionally runs only registry, configuration, and
capability checks.

Every `DoctorCheck` has a `PASS`, `WARNING`, or `ERROR` status, a stable name,
a concise message, and optional safe detail. `DoctorReport.to_json()` provides
machine-readable output; `to_text()` provides deterministic human output.

```python
report = DoctorService(manager).run()
print(report.to_text())
assert report.errors == 0
```

Doctor never prints API key values, raw headers, or raw provider error bodies.
