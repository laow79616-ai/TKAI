# TKAI V7 Foundation Architecture

V7 is an opt-in architecture layer under `tkai.v7`. It does not replace or
monkey-patch V6, and importing it performs no registration, network access,
migration, or background work.

The kernel is the composition root. Modules declare contracts and capabilities;
registries expose metadata; the service container provides dependency injection
and discovery; the lifecycle manager controls deterministic startup and shutdown.
Events and observability are local hooks so deployments may select their own
backends.

The foundation packages are intentionally domain-neutral. Existing TikTok
modules continue to use their V6 paths and behavior.

## Boundaries

- `contracts`, `interfaces`: stable types and version negotiation.
- `kernel`, `runtime`, `context`: composition and lifecycle.
- `registry`, `modules`, `services`: capabilities, extensions, and injection.
- `observability`, `security`, `configuration`: cross-cutting safeguards.
- `compatibility`, `migration`: opt-in V6 adapters and manual planning.
- Remaining packages define future extension boundaries without implementations.

Dependencies point inward toward contracts. Business modules depend on the
kernel interfaces; the kernel never imports a business module.
