# Package Service

The Sprint-1 top-level `server.ReferencePackageService` remains the generic
architecture reference service. The concrete Package Foundation is available
at `server.package.ReferencePackageService`, with its own
`server.package.PackageStorage` protocol and `ReferencePackageStorage`.

Both forms are local-only references: they have no package upload, download,
artifact, filesystem, database, Registry, Publisher, or network behavior.
