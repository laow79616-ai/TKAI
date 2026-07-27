# Enterprise AI Business Intelligence Architecture

`business_intelligence` is a framework-neutral, in-memory reference control
plane. Every record carries tenant and workspace scope. The service layer
enforces RBAC, isolation, safe expressions, query/export limits, credential
references, audit records, and Prometheus-compatible metrics. External database,
warehouse, lakehouse, rendering, forecasting, mapping, delivery, row-security,
column-security, and masking implementations attach through bounded interfaces.

The API facade exposes resources beneath `/business-intelligence`. The dashboard
uses the same scoped facade and never receives credentials.
