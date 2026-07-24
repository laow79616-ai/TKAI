# Cloud Storage Foundation

The Storage Foundation is reference-only. It supplies immutable storage, bucket,
object, context, capability, quota, lifecycle, registry, factory, policy, and
result descriptors with an in-memory service. It never touches a local disk,
network, S3, Azure Blob, GCS, MinIO, database, Shell, credentials, or provider
SDK. Buckets and objects are metadata declarations, not file handles or data.
