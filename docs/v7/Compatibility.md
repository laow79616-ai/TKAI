# V6 Compatibility

V6 remains the default public package and retains version `6.0.0`. V7 is
available only from `tkai.v7`.

`adapt_v6_module()` wraps legacy `activate(context)` and
`deactivate(context)` objects in the V7 lifecycle. The adapter is explicit:
V7 never scans for, replaces, imports, or activates V6 modules automatically.
Existing TikTok imports and APIs are unchanged.

Compatibility adapters should translate at the boundary and delegate to the V6
implementation. They must not reimplement V6 business rules.
