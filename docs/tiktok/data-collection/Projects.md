# Projects

A collection project contains ID, name, description, tenant, workspace, owner,
configured source reference, dataset reference, lifecycle status, version, and
metadata. Source and dataset references must resolve within the same tenant and
workspace. IDs are immutable and unique in the service.

Metadata is descriptive only. Keys associated with passwords, secrets, tokens,
cookies, or credentials are rejected. Projects become runnable only after their
source, dataset, filters, and pipeline configuration has been validated.
