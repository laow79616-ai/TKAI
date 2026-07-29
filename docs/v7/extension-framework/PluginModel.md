# Plugin Model

A plugin is a scoped child manifest declared by a parent extension. It carries
its own plugin ID, identity, version, compatibility, dependencies, permissions,
capabilities, interfaces, lifecycle, status, health, metrics, audit references,
and sandbox boundaries.

Registration requires a registered parent in the same tenant, workspace, and
namespace, and the plugin ID must appear in the parent manifest. The V6 plugin
API remains available unchanged.
