# Enterprise AI Digital Twin Architecture

The `digital_twin` package is a framework-neutral control plane layered alongside
TKAI's existing enterprise platforms. It models tenant/workspace-scoped twins,
entities, topology, state, synchronization, telemetry, simulations, predictions,
and optimizations. External event streaming, models, storage, schedulers, and
optimizers integrate through adapters; the reference implementation performs no
external I/O and does not replace existing platform services.

The API facade exposes `/digital-twins`, `/entities`, `/relationships`, `/state`,
`/simulation`, `/predictions`, and `/optimization`. Dashboard projections cover
twins, topology, telemetry, simulation, predictions, optimization, and metrics.
