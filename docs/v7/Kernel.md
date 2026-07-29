# V7 Kernel

Create `tkai.v7.Kernel`, register modules and services explicitly, then call
`start()` and `stop()`. A new kernel has no business modules and no external
effects.

Services are registered using `ServiceDescriptor` plus either an instance or a
factory. Factories receive the resolver and may request other registered
interfaces. Discovery returns descriptors, not service internals.

Modules declare a `ModuleDescriptor`. Registration checks kernel-version
compatibility, records capabilities, and creates a deny-by-default isolation
grant containing only the declared capabilities.
