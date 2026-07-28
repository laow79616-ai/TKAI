# Storage

The catalog stores encrypted dataset references, not dataset payloads. Supported
operations are Import, Export, Archive, and Restore. Every operation validates
tenant and workspace scope, requires the `tiktok:data:storage` permission, and
writes an audit event.

Retention is part of the dataset definition. Production storage services must
enforce deletion and archival schedules independently and publish completion
events. Logs may include dataset IDs and opaque `kms://` or `vault://`
references, but must never include keys, credentials, tokens, cookies, or
decrypted payloads.
