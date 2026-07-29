# V8 Governance Compatibility

Compatibility records connect governance references across V6, V7, and V8.
References retain their generation, identifier, version, URI, kind, and
metadata. The fabric does not require V6 or V7 owners to change their public
interfaces and does not write back to any generation.

The compatibility projection is safe to use during staged migrations because it
is additive, read-only, and isolated from runtime lifecycle state.
