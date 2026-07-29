# Hyper Kernel

`tkai.v8.kernel.HyperKernel` has stable ID
`uuid5(229e1e20-b57e-4f34-b33c-999927c03c8a, "tkai-hyper-kernel:8.0.0")`
and version `8.0.0`.

It provides registration and discovery of metadata, dependency references,
lifecycle labels, aggregated published health, structured diagnostics, metrics,
tracing hooks, structured logs, and append-only audit metadata. There is
intentionally no `execute`, `dispatch`, `publish`, or TikTok action method.

Applications may instantiate isolated kernels or include the GET-only router.
Registration does not import or call the referenced implementation.
