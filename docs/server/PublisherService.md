# Publisher Service

The Sprint-1 top-level `server.ReferencePublisherService` remains the generic
architecture reference service. The concrete Publisher Foundation is available
at `server.publisher.ReferencePublisherService`, with its own
`server.publisher.PublisherStorage` protocol and `ReferencePublisherStorage`.

Both forms are local-only references: they have no account management,
authentication, authorization, verification, package upload, artifact,
filesystem, database, or network behavior.
