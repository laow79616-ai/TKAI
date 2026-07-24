# Search Service

The Sprint-1 top-level `server.ReferenceSearchService` remains the generic
architecture reference service. The concrete Search Foundation is available at
`server.search.ReferenceSearchService`, with its own
`server.search.SearchStorage` protocol and `ReferenceSearchStorage`.

Both forms are local-only references: they do not crawl, index, use a search
engine, access a database or network, or mutate other Server domains.

The concrete `server.search.ReferenceSearchService` also exposes its immutable
local `events()` sequence for read-only lifecycle validation. It does not
publish events or start an event consumer.
