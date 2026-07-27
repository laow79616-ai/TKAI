# Messaging

`QueueInterface` bounds topic publication, consumer-group subscription,
acknowledgement, and queue-depth reporting. Retry and dead-letter behavior is
configured by the control plane; broker-specific ordering and delivery
guarantees remain explicit adapter capabilities.
