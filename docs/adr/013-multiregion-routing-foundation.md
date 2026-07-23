# ADR 013: Multi-region Routing Foundation

Use immutable Region metadata, a separate Topology, and explicit adapters. This
keeps single-region behavior as the default and makes ordering deterministic
without adding infrastructure routing dependencies. No automatic failover or
traffic movement is performed because the local process lacks global health and
capacity authority.
