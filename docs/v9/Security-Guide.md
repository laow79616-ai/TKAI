# V9 Security Guide

V9 enforces RBAC and tenant, workspace, namespace, framework, and profile
isolation at registry boundaries. Metadata validation rejects unsafe values,
secret filtering protects diagnostics, and audit records retain correlation.
Runtime governance observes pause, maintenance, and kill-switch state.

The V9 public surface is GET-only. It exposes no credentials, secret values,
hidden reasoning, chain of thought, scratchpads, execution, runtime mutation,
configuration apply, workflow start, scheduler mutation, service control,
resource allocation, recovery execution, snapshot restoration, rollback,
migration, upgrade, automatic approval, extension installation, plugin loading,
or deployment execution endpoint.
