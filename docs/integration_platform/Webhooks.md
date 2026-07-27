# Webhooks

Inbound and outbound webhook registrations use secret references. Inbound
verification applies bounded bodies, HMAC-SHA256 signature validation,
constant-time comparison, and nonce replay protection. Delivery history records
only correlation metadata and outcomes. Exhausted deliveries belong in the
tenant-scoped dead-letter collection.
