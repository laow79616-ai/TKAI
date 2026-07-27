# Datasets

Datasets define an ID, schema name, unique fields, tags, version, retention in
days, record count, and encrypted storage reference. Storage references must use
the `kms://` or `vault://` schemes. The control plane never persists encryption
keys or raw storage credentials.

Successful collection increments record count and dataset version. Retention is
validated from 1 to 3,650 days. Import, export, archive, and restore are audited
storage operations; archive and restore update the catalog state.
