# Unified Capability Framework Architecture

The V7 capability framework is an opt-in control plane under
`tkai.v7.capabilities`. It does not modify V6 runtime paths or existing TikTok
business behavior.

Descriptors enter the global or an isolated registry, are validated, resolved
through a dependency graph, loaded in topological order, and managed through a
guarded lifecycle. Health, metrics, audit, catalog, dashboard, and GET-only API
views read the same registry snapshots. Providers are supplied explicitly;
import-time scanning and automatic activation are intentionally prohibited.
