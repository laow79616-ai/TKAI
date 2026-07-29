# Routing

`ServiceRouter` builds a deterministic routing table from the registry. It
considers only running services and, by default, only endpoints whose latest
health state is available. Candidates sort by numeric priority, service ID, and
reference, making selection stable across runs.

Routes return references only. Callers can provide an ordered list of fallback
interfaces. No DNS, HTTP, sockets, service proxy, or external networking is
implemented.
