# V8 Governance Approvals

Approval records describe a subject, approver references, status, review
references, audit references, and metadata. They are reference-only governance
evidence.

An approval never authorizes execution. `ApprovalRecord.execution_authorized`,
the governance helper, and the fabric execution-approval capability all return
`False`. Runtime components must not treat these records as credentials,
capability grants, or action approvals.
