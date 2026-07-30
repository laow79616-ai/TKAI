# Hyper Reasoning Evidence

Evidence records store identifiers, source and subject references, provenance
metadata, and optional reliability values. Evidence payloads and live source
connections are outside the fabric.

`EvidenceAggregator` accepts reference descriptors for V8 Hyper Knowledge, V8
Hyper Intelligence, all other V8 Frameworks, all V7 Frameworks, and all V6 AI
Centers. Aggregation normalizes and sorts descriptors without invoking or
mutating referenced components.

Reliability values are optional and constrained to the inclusive range 0–1.
Diagnostics report unresolved evidence references as informational findings.
