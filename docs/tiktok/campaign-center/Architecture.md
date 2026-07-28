# TikTok Campaign Center Architecture

The Campaign Center is a local, single-user coordination control plane. It owns
campaign identity, lifecycle, plans, schedules, approvals, monitoring snapshots,
analytics views, and immutable history. It does not own publishing, workflow,
automation, execution, analytics collection, or TikTok connectivity.

Dependencies are inverted through bounded `Protocol` ports. Campaign plans store
only opaque `ref://` or encrypted `kms://`/`vault://` references. Existing Creator
Workspace, Content Center, Publishing Center, Workflow Center, Automation Engine,
Execution Engine, Analytics Center, Operations Planner, and decision systems
remain the systems of record.

Starting a campaign registers its approved plan with the Operations Planner. This
is a coordination handoff only; it never publishes or executes directly.
