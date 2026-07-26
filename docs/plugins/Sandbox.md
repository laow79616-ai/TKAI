# Plugin Sandbox

`PluginSandbox` executes trusted local callables with an explicit policy.
Policies describe filesystem roots, network hosts, environment keys, a timeout,
and a memory ceiling. The default policy grants no access. Timeout enforcement
isolates work on a dedicated executor. The memory limit is a policy contract;
production process or container runtimes must enforce it at the OS boundary.
