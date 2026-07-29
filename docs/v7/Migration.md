# V7 Migration

Migration is scaffolding only. `MigrationPlan` stores documented steps and its
`execute()` method always refuses automatic execution.

Recommended manual sequence:

1. Inventory a V6 integration and its observable behavior.
2. Define the interface and capability contract.
3. Wrap the V6 object with a compatibility adapter.
4. Validate equivalent behavior with mocks and regression tests.
5. Opt in one deployment at a time with an explicit rollback plan.

No data, configuration, or module migration runs when V7 is imported or started.
