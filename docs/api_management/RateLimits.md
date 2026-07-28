# Rate Limits

Rate limits can target tenants, consumers, or routes and bound requests per
second, requests per minute, burst, and concurrency configuration. Values must
be positive and no larger than one million. Rejections increment a dedicated
metric.
