# V8 Hyper Coordination Framework

The Hyper Coordination Framework is TKAI's advisory, metadata-driven
cross-framework coordination layer. It catalogs profiles, framework and
capability references, dependencies, relationships, lifecycle state,
compatibility, health, metrics, audit evidence, and governance references.

It has no executor, TikTok adapter, dispatcher, or runtime mutation API.
`approved_reference` means only that referenced metadata passed its recorded
governance review; it never authorizes execution.

Profiles are immutable and isolated by tenant, workspace, and framework.
The default registry references the V8 Hyper Kernel, all V7 frameworks, all V6
AI Centers, and a future-framework extension point.
