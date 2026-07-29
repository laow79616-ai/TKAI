# Recovery

Recovery and rollback plans coordinate IDs, strategies, target URIs, readiness,
issues, and audit entries. Targets must be references such as snapshot URIs.
Deleted resources are not recovery-ready.

Plans do not restore data, restart workers, launch browsers, or invoke resource
providers. An external authorized recovery system may consume the metadata.
