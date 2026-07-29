# Capability Model

A capability has an ID, name, description, owner, semantic version, category,
status, dependencies, interfaces, permissions, health, metrics, audit records,
tags, metadata, configuration, upgrade paths, deprecation metadata, and
lifecycle history.

IDs are stable and whitespace-free. Dependencies declare compatible semantic
version ranges and may be optional. Configuration is never emitted by the
public serializer. Metadata, diagnostics, and audit details are recursively
filtered for secret-shaped keys.
