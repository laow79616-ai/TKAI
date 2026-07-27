# Decision Lifecycle

The controlled lifecycle is:

`draft → proposed → under_review → approved → executed → archived → deleted`

Reviewers may reject an item under review. A rejected decision can be revised
and proposed again or archived. Approval requires at least one completed
approval record. Every transition is tenant-scoped, authorized, timestamped,
and audited. Execution increments the success counter and records end-to-end
decision latency.
