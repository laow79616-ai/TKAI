# Authentication

Password, OIDC, OAuth2, LDAP, SAML, and MFA are provider interfaces so deployments
can use approved enterprise identity systems. API keys and service tokens are
compared by digest and are never returned. Failed attempts are metered, audited,
and passed to brute-force detection.
