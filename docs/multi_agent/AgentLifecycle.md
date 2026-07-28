# Agent Lifecycle

Agents progress through Draft, Provisioned, Ready, Running, Paused, Completed,
Archived, and Deleted states. The transition map rejects unsafe jumps.
Provisioning validates identity, owner, role, capabilities, tenant, workspace,
version, and metadata. Deleted agents are terminal.
