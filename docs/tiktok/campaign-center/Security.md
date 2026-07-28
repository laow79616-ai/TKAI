# Campaign Center Security

Every command and query requires a `CampaignScope` containing tenant, workspace,
actor, and RBAC permissions. Stored records are checked against both tenant and
workspace. Approval is enforced before approval and running transitions.

External references must use opaque `ref://` or encrypted `kms://`/`vault://`
forms. Password, secret, token, cookie, and credential keys are rejected from
metadata. Audit records contain actor, action, scope, resource, and timestamp but
never secret values.

The module provides no CAPTCHA bypass, restriction circumvention, anti-detection
guarantee, spam automation, or platform-security bypass.
