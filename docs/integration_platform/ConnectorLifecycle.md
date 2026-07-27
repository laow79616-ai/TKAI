# Connector Lifecycle

Integrations move through Draft, Configured, Validated, Enabled, Disabled,
Failed, Archived, and Deleted states using an explicit transition table.
Execution is allowed only while Enabled. Configuration changes require
`integration:write`; validation and provider-specific runtime checks belong to
bounded adapters. Archived records may only be deleted.
