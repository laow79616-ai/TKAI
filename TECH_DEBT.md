# Technical Debt

## Planned work

- Built-in plugin manifests currently provide lifecycle-compatible integration
  placeholders; production adapters for Docker, Git, messaging, and social
  services still need capability-specific commands and credential handling.
- AI providers intentionally use injected transport clients. Official SDK
  adapters, streaming responses, tool calling, rate-limit handling, and secret
  storage remain future work.
- Parallel workflows share one mutable context. Introduce immutable inputs or
  synchronization primitives before supporting writes from parallel tasks.
- Workflow scheduling is in-process only; persistence, cancellation, timeout,
  and distributed execution are not yet implemented.
- The repository retains an unrelated top-level `core/` prototype directory;
  it is excluded from package tooling and should be removed only through a
  dedicated migration after confirming external consumers do not rely on it.
