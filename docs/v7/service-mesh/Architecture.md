# V7 Unified Service Mesh Architecture

The V7 service mesh is an opt-in, in-process framework for internal TKAI
services. It adds no network proxy, listener, external discovery system, or
TikTok behavior. V6 modules continue to load without the mesh.

The immutable service model feeds the registry and metadata indexes. Discovery
and dependency resolution read the registry. The router selects only running,
healthy services and returns opaque internal references. Lifecycle coordinates
providers in dependency order. Health, metrics, structured logs, trace hooks,
events, and audit records are transport-neutral and in memory by default.

Applications explicitly register service providers and may expose the read-only
API or dashboard projection. Nothing is auto-discovered or auto-started.
