# Hyper Decision Architecture

TKAI V8 Hyper Decision is an immutable, metadata-driven coordination layer spanning
V6 AI Centers, V7 Frameworks, and V8 Frameworks. Its contracts, isolated registries,
observability projection, dashboard, and GET-only API are deliberately separated
from runtime orchestration. It never invokes TikTok, mutates runtime state, authorizes
execution, or performs automatic approval.

The composition root is `HyperDecisionFabric`. Records are frozen dataclasses;
registries key records by tenant, workspace, decision namespace, and identifier.
References preserve generation, version, framework, URI, and safe metadata.
