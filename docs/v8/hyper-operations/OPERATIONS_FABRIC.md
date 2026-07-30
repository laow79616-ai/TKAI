# Operations Fabric

Operation profiles join operation, workflow, resource, runtime, readiness, governance, compatibility, health, metric, audit, and arbitrary safe metadata references. Summaries describe operations, workflows, runtimes, dependencies, resources, and recovery, including version history.

All records are frozen dataclasses. Registration affects only the fabric's local metadata catalog; it does not change any referenced runtime.
