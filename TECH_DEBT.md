# Technical Debt

## Planned work

- Built-in plugin manifests currently provide lifecycle-compatible integration
  placeholders; production adapters for Docker, Git, messaging, and social
  services still need capability-specific commands and credential handling.
- AI providers support injected transports, async streaming normalization,
  capability declarations, and offline fallback policy. Official SDK adapters,
  durable secret storage, dynamic provider health probing, configurable
  fallback policy loading, and production credential discovery remain future
  work.
- Provider configuration construction from project YAML/JSON and environment
  expansion is application-owned pending configuration schema consolidation.
- Parallel workflows share one mutable context. Introduce immutable inputs or
  synchronization primitives before supporting writes from parallel tasks.
- Workflow control and JSON checkpoint recovery are in-process only; durable
  storage, distributed execution, and forced termination of synchronous
  handlers remain intentionally out of scope for V1.0.
- The repository retains an unrelated top-level `core/` prototype directory;
  it is excluded from package tooling and should be removed only through a
  dedicated migration after confirming external consumers do not rely on it.
