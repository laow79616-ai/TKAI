# Application Lifecycle

Applications move through `draft`, `submitted`, `under_review`, `approved`,
`published`, `suspended`, `deprecated`, `archived`, and `deleted`. The transition
map rejects skipped or terminal transitions. Publishing actions require the
scoped `publish` permission; approval and suspension require `moderate`. Every
accepted transition is audited with secrets redacted.
