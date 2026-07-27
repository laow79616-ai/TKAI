# Credentials

Credential objects store only `secret://`, `vault://`, or `kms://` references.
Supported references cover API keys, OAuth2 grants, service accounts,
certificates, and external secret stores. Rotation updates audit metadata but
never reads or logs secret values. Resolution is a deployment responsibility.
