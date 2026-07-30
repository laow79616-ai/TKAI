# V9 Compatibility Guide

V9 supports V6.0.0, V7.0.0, V8.0.0, and V9.0.0 contracts. Compatibility
adapters negotiate versions and expose metadata without changing existing
TikTok modules, routes, storage, configuration, extensions, dashboards,
AI Studio, local runtime, security, or deployment behavior.

Existing callers may continue using their versioned APIs unchanged. New V9
consumers should treat recommendations, plans, recovery information, and
migration information as advisory. There are no apply, execute, start,
schedule, install, restore, rollback, migrate, or upgrade operations.
