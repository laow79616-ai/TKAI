# TikTok Account Center architecture

The Account Center is the TikTok Cloud Control Platform identity control plane. It reuses TKAI's API gateway, workflow and automation runtimes, browser runtime, event streaming, security, observability, knowledge, memory, reasoning, command center, and multi-agent runtime. The domain service is framework-neutral and is registered under `/tiktok`.

Every entity carries tenant and workspace ownership. RBAC is checked before access and every mutation creates an audit record. Browser bindings contain references only. Account login state is encrypted at rest and is never returned by models, APIs, dashboards, metrics, logs, or audit events.
