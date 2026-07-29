# V8 Governance Policies

Policy records contain a stable ID and name plus references to frameworks,
rules, and constraints. Relationships can connect policies to other governance
records across versions.

Policy data is advisory. `PolicyRecord.enforced` and
`PolicyFabric.enforces_policies()` always return `False`. Consumers must not
translate policy metadata into runtime permission or execution authority.
