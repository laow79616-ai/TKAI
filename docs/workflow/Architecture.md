# Enterprise Workflow Platform Architecture

## Architecture

`workflow_platform` is a transport-neutral domain package integrated into the
optional TKAI FastAPI host. It contains isolated workflow and execution stores,
a deterministic bounded engine, visual-designer contracts, a template catalog,
human-task primitives, connector interfaces, dashboard projections, metrics,
and HTTP route registration.

## Designer

The designer models canvas coordinates, grouping, drag-and-drop node updates,
edges, graph validation, immutable versions, undo, and redo. Publication requires
one start node, at least one end node, and valid edge references. Zoom and canvas
rendering remain presentation concerns driven by node positions.

## Execution

The engine supports sync and async request contracts, bounded retry and timeout,
per-node checkpoints, resume offsets, rollback, cancellation, and durable
in-process history. Node handlers integrate Agents, Tools, Plugins, nested
Workflows, Webhooks, HTTP, Knowledge, RAG, Models, and Custom nodes without
hard-coding those preserved platform implementations.

## Nodes

The registry includes Start, End, Agent, Tool, Plugin, Workflow, Condition,
Switch, Loop, Delay, Approval, Form, Webhook, HTTP, Knowledge, RAG, Model, and
Custom. Built-in control nodes are deterministic; integration nodes use
explicitly registered handlers.

## Variables

Inputs, outputs, environment, workflow, and runtime values use namespaced
`${namespace.key}` expressions. `${secret.name}` yields only an opaque secret
reference. Arbitrary Python or shell expressions are never evaluated.

## Approvals and Forms

Approval steps support users, teams, roles, timeouts, escalation destinations,
and append-only decisions. Forms use a bounded JSON-schema subset with required
fields, primitive validation, defaults, and an attachment interface flag.

## Templates

Templates have categories and search, plus import, export, and clone operations.
A clone resets lifecycle/version and moves into the caller's isolated scope.

## Security

Every workflow and execution is tenant/workspace scoped. Permission validation
is explicit and audited. Sensitive audit fields are redacted, secrets remain
references, and retries, timeouts, histories, schedules, and connector result
counts are bounded. Production adapters must supply durable encrypted stores,
distributed scheduling, and approved network connector implementations.
