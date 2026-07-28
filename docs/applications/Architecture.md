# Enterprise AI Application Center Architecture

The Application Center is additive to Agent Runtime, Plugin Marketplace,
Enterprise Platform, Cloud Native, AI Studio, and Enterprise Marketplace.
Catalog owns definitions; templates provide starting points; versions capture
publication snapshots; deployment and runtime provide scaling, execution,
quota, audit, and metrics. Existing Docker, Kubernetes, CI/CD, and
observability infrastructure is preserved.

FastAPI exposes `/applications`, `/templates`, `/deployments`, and application
version endpoints. The dashboard exposes Applications, Templates, Deployments,
Usage, Versions, and Permissions views.
