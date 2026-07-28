# TikTok Resource Center Architecture

The Resource Center is the local inventory and allocation control plane for TKAI
TikTok resources. `models.py` defines bounded contracts, `service.py` owns lifecycle
coordination, `adapters.py` exposes read-only discovery ports, `metrics.py` reuses
Prometheus conventions, and `api/` registers transport-neutral HTTP handlers.

The center stores references, not platform credentials. Existing Account, Browser
Runtime, Browser Cluster, Device, Proxy, Scheduler, Workflow, Operations, and Risk
Control modules remain the systems of record. Adapters may discover their safe
resource summaries; all operations remain subject to those modules' controls.

The implementation is single-user and local but enforces tenant and workspace scope
at every service boundary. It neither automates TikTok protection challenges nor
bypasses platform restrictions.
