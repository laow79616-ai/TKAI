# Agent Tool Registry

Each tool declares a schema, required permission, timeout, retry policy, and
immutable metadata. Lookup checks the caller's explicit permission set.
Registration never imports, discovers, or executes a tool automatically.
Hosts remain responsible for enforcing timeouts and invoking handlers through
their established workflow execution policy.

