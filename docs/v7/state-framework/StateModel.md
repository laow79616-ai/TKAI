# State Model

`StateRecord` includes identity, type, owner, monotonically increasing version,
lifecycle, current and previous state, transition history, snapshot reference,
filtered metadata, health, metrics, audit references, dependencies, tenant and
workspace scope, and timestamps. Contracts are frozen dataclasses. Secret-like
metadata keys are redacted at construction.
