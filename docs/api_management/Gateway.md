# Gateway

Routes use longest-prefix path and HTTP method matching. Each route references
an upstream through `service://` or HTTPS, and exposes bounded load-balancing,
timeout, retry, circuit-breaker, health-check, request-size, and response-size
configuration. Runtime integrations provide the actual upstream transport.
