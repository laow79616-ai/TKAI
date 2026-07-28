# Approvals

An approval workflow names its reviewers and begins in `pending`. Only an
assigned reviewer with the approval permission can approve or reject it.
Reviews append the reviewer, outcome, comment, and timestamp to the decision
log. The platform also emits a sanitized audit event. Production adapters can
map this contract to Enterprise Workflow Platform tasks and policy-controlled
quorum rules.
