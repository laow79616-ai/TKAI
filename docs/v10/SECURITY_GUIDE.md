# V10 Security Guide

V10 uses existing authentication and RBAC boundaries plus tenant, workspace,
namespace, framework, profile, and trust-domain scope checks. Metadata is
validated and secret-like keys are filtered before projection or logging.
Audit correlation covers advisory reads.

The V10 API is GET-only. It exposes no execution, mutation, service control,
scheduler control, migration, upgrade, rollback, restore, deployment,
extension installation, secret retrieval, hidden prompt, chain-of-thought, or
private scratchpad endpoint. Pause, maintenance, and kill-switch state is
observed as metadata and is never overridden.
