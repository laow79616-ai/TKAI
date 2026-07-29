# Knowledge Versioning

Versions are append-only records numbered within a tenant, workspace, and
profile. They contain the refined summary, confidence, evidence, explanation,
predecessor reference, and UTC creation time.

Comparisons require two versions from the same profile and report whether the
summary changed, the confidence delta, and an explanation. Comparisons never
replace or delete versions.
