# V6 Compatibility

The V7 distribution version is `7.0.0`; the V6 compatibility surface remains
available and V7 frameworks are opt-in under `tkai.v7`.

`adapt_v6_module()` wraps legacy `activate(context)` and
`deactivate(context)` objects in the V7 lifecycle. The adapter is explicit:
V7 never scans for, replaces, imports, or activates V6 modules automatically.
Existing TikTok imports and APIs are unchanged.

The V6 and V7 API routes, Dashboard, AI Studio, local runtime, deployment
profiles, configuration sources, storage adapters, extension contracts, and
OpenAPI contracts remain compatible. Final release validation treats any
removed route, changed execution default, automatic migration, or newly public
mutation endpoint as a blocker.

Compatibility adapters should translate at the boundary and delegate to the V6
implementation. They must not reimplement V6 business rules.
