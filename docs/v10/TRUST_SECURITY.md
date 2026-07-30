# Trust Mesh Security

Metadata reads require a reader, auditor, or trust-metadata-reader role
reference and matching tenant, workspace, and namespace. Trust-domain
identifiers must also match. Secret-bearing keys are rejected at registration
and filtered from responses. Registration emits audit, structured-log, and
trace metadata. The framework stores no credentials and takes no TikTok action.
