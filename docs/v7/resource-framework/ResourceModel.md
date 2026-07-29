# Resource Model

`Resource` is immutable and identifies a resource by ID, normalized type,
category, owner, semantic version, and tenant/workspace scope. It contains
state metadata, capacity, availability, an optional reservation reference,
dependency references, constraints, lifecycle, health, metrics, audit
references, capabilities, tags, and secret-filtered metadata.

Built-in types are account, browser, browser profile, device, proxy, worker,
queue, storage, scheduler, workflow, capability, service, extension, and
module. Register a `ResourceTypeContract` before using a future type.

Lifecycle states are registered, validated, available, reserved, planned,
unavailable, paused, recovering, archived, and deleted. Transitions are
explicit and metadata-only.
