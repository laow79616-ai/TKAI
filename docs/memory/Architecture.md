# Enterprise AI Memory Engine Architecture

`memory_engine` is a transport-neutral, dependency-light domain package. The
service coordinates typed memory objects, a bounded read/write-through cache,
an in-memory retrieval index, retention policy, compression helpers, namespace
catalog, RBAC, audit, and metrics. `server.api.app` owns HTTP wiring so the
engine remains usable by agents, workflows, applications, and plugins without
requiring FastAPI.

The included stores and index are deterministic reference implementations.
Production adapters can replace them behind the service boundaries without
changing memory objects or API contracts.
