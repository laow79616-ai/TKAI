# TKAI V11 API Guide

`GET /v11` returns the platform inventory. Each component is available at
`GET /v11/{component}` with `overview`, `health`, `diagnostics`, `metrics`, and
`audit` projections. Specialized intelligence, knowledge-graph, and reasoning
routes remain available. All V11 operations are advisory and GET-only.
