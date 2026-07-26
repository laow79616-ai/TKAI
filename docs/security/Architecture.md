# Enterprise AI Security Platform Architecture

The security platform is a dependency-free, tenant and workspace scoped security
domain integrated with the TKAI API, dashboard, packaging, and Prometheus
endpoint. It uses host-provided adapters for identity protocols, vaults,
encryption, anomaly detection, scanning, firewall enforcement, and sandboxes.

Domain services never store plaintext passwords, API keys, service tokens, secret
values, or encryption keys. Only external references and one-way credential
digests are retained. Every security operation emits a scoped audit event.
