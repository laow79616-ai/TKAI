# Registry Service

The Sprint-1 top-level `server.ReferenceRegistryService` remains the generic
architecture reference service. The concrete Registry Foundation is available
at `server.registry.ReferenceRegistryService`, with its own
`server.registry.RegistryStorage` protocol and `ReferenceRegistryStorage`.

Both forms are local-only references: they have no remote Registry, download,
upload, artifact, filesystem, database, or network behavior.
