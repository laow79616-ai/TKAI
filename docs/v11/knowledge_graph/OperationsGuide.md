# Operations Guide

No graph service, database, worker, or scheduler needs to be operated. The graph
is built in process from immutable metadata when the optional API host is created.

Operators can inspect `/v11/graph/health`, `/metrics`, `/validation`, and
`/diagnostics`. Healthy metadata has known edge endpoints, unique IDs, matching
scope, and no unsafe metadata.

A degraded or rejected snapshot must be corrected in source and redeployed through
the normal reviewed release process. The graph cannot repair, mutate, optimize, or
reload itself. Audit data is a projection and cannot be appended through this
feature.
