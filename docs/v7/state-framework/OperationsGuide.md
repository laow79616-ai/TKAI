# Operations Guide

1. Construct a scoped immutable state and register it explicitly.
2. Advance lifecycle using the current version as `expected_version`.
3. Create reference-only snapshots at operational checkpoints.
4. Review consistency and health projections.
5. Simulate recovery and review readiness before any owner-controlled action.
6. Inspect metrics, traces, transition history, recovery history, and audit.

The HTTP surface is GET-only at `/v7/state/*`; runtime mutation is not exposed.
