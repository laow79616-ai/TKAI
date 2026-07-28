# Allocations

Allocations bind a workspace resource to an owner at a bounded priority. A matching
reservation is required when the resource is reserved. Release validates ownership,
deactivates associated leases, records a bounded cooldown, and returns the resource
to `released`. Active TikTok restrictions or challenges block allocation.
