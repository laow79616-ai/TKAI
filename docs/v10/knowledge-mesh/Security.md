# Security

Reads require a reader, auditor, or knowledge-metadata-reader role and exact
tenant/workspace/namespace scope compatibility. Registries enforce scope
isolation and bounded capacity. Secret-bearing metadata is rejected at
registration and filtered at serialization. Reads and registrations generate
local audit, trace, and structured-log metadata.
