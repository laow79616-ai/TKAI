# Version Service

The Sprint-1 top-level `server.ReferenceVersionService` remains the generic
architecture reference service. The concrete Version Foundation is available
at `server.version.ReferenceVersionService`, with its own
`server.version.VersionStorage` protocol and `ReferenceVersionStorage`.

Both forms are local-only references: they have no release pipeline, package
upload, artifact, filesystem, database, Registry, Publisher, or network
behavior.
