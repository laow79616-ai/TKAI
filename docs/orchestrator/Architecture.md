# Enterprise AI Orchestrator Architecture

The orchestrator is a tenant-scoped control plane over existing TKAI agents,
applications, workflows, knowledge, tools, and plugins. The planner creates an
immutable execution plan; scheduler and queues stage work; coordinator enforces
resource limits; router selects registered adapters; executor runs steps and
persists checkpoints; recovery restores or compensates state. Events, audit
records, dashboard views, and Prometheus metrics expose every lifecycle stage.

Core code remains dependency-free. FastAPI registration is optional and uses
the established server application factory.
