# Operations Guide

Inspect `/v9/planning/health`, `/v9/planning/metrics`, diagnostics, and audit
projections for operational status. All endpoints are GET-only and expose local
metadata. A degraded source should be corrected upstream and its reference
reviewed; the mesh must not repair or mutate that source.
