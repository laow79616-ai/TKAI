# Campaign Plans

Plans connect a campaign to existing publishing, workflow, automation, execution,
content, and schedule records. References are validated through tenant- and
workspace-scoped read-only adapters. Dependencies may reference only plans already
registered for the same campaign.

The Campaign Center does not copy external records and does not invoke a browser,
device, account, proxy, workflow, publisher, or executor. Approved plans are
handed to the Operations Planner through its bounded planning interface.
