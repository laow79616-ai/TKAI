# TKAI Business Platform V2 Database Guide

Set `TKAI_BUSINESS_DATABASE` to the local SQLite file. On first start, schema version
2 creates `business_records`, `business_audit`, and `business_settings`, including
scope and module indexes. Existing files are initialized idempotently and never
dropped or rewritten. Back up before upgrades. Records use scoped primary keys,
UTC timestamps, JSON metadata, and an archive flag. Audit rows are append-only.
