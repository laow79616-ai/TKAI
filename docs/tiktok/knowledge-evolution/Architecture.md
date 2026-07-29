# TikTok Knowledge Evolution Center Architecture

The Knowledge Evolution Center is an in-process, read-only refinement layer for
the local single-user TikTok Cloud Control Platform. Tenant and workspace scoped
profiles select bounded sources. Aggregation produces integrity-referenced
evidence, evolution produces immutable versions, comparisons explain changes,
and recommendations remain advisory.

The layer exposes no execution, publishing, configuration, or TikTok restriction
bypass port. Source adapters have one read method. The HTTP surface is GET-only.
Service curation methods populate local knowledge records for trusted internal
orchestration and tests; they never mutate a source module or runtime settings.

Security is enforced at every service boundary with RBAC, tenant isolation,
workspace isolation, audit records, bounded payloads, and secret-key rejection.

The package boundaries are profiles, knowledge, sources, evolution, versions,
comparisons, confidence, recommendations, history, analytics, dashboard, and API.
